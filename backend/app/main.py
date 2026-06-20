import os
import httpx
import logging
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ПОЛНОСТЬЮ ОБНОВЛЕННЫЙ СПИСОК БЕСПЛАТНЫХ МОДЕЛЕЙ
FREE_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2.5-7b-instruct:free"
]

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return None
    try:
        conn = psycopg2.connect(db_url, connect_timeout=3)
        return conn
    except Exception as e:
        logger.error(f"Не удалось подключиться к БД: {e}")
        return None

@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("База данных успешно проверена.")
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы: {e}")

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        raw_user_message = data.get("text") or ""
        image_base64 = data.get("image") or ""
        mode = data.get("mode") or "private"
        client_history = data.get("history") or []
        client_time = data.get("clientTime") or "Неизвестно"
        
        # Очищаем текст сообщения для ИИ и для базы данных от системного мусора [Системное инфо...]
        user_message = re.sub(r"^\[Системное инфо\..*?\]\s*", "", raw_user_message, flags=re.DOTALL)
        user_message = re.sub(r"^\[Текущие дата и время.*?\]\s*", "", user_message, flags=re.DOTALL)
        user_message = user_message.strip()

        # Автоматически вытаскиваем реальное имя гостя из скрытой строки фронтенда
        guest_name = "Пользователь"
        if "Имя собеседника:" in raw_user_message:
            match = re.search(r"Имя собеседника:\s*([^\s\]]+)", raw_user_message)
            if match:
                guest_name = match.group(1)

        # Вытаскиваем точную дату из строки
        time_info = f"Текущие дата и время у пользователя (МСК): {client_time}.\n\n"
        if "Текущие дата и время:" in raw_user_message:
            time_match = re.search(r"Текущие дата и время:\s*([^\]\n]+)", raw_user_message)
            if time_match:
                time_info = f"Текущие дата и время у пользователя (МСК): {time_match.group(1)}.\n\n"

        # Требование по ссылкам для системного промпта
        web_search_instruction = (
            "Если пользователь просит найти что-то на сайтах или зайти по ссылке — "
            "используй свои внутренние знания, читай информацию и ОБЯЗАТЕЛЬНО в конце своего ответа "
            "давай точные ссылки (URL) на сайты, о которых идет речь."
        )

        # 1. НАСТРОЙКА СИСТЕМНЫХ ПРОМТОВ В ЗАВИСИМОСТИ ОТ РЕЖИМА
        if mode == "public":
            system_prompt = (
                f"{time_info}"
                f"Ты — крутой, вежливый и отзывчивый ИИ-помощник. Твой стиль общения — живой, "
                f"свободный, понятный и по-человечески теплый. Никакой лишней официальщины. "
                f"Отвечай всегда только на русском языке, просто и емко. Не расписывай длинные простыни текста.\n"
                f"{web_search_instruction}\n"
                f"ВАЖНО: Твоего собеседника зовут {guest_name}. Обращайся к нему по этому имени! "
                f"Не используй имя Алексей, сейчас ты общаешься именно с пользователем по имени {guest_name}."
            )
        else:
            system_prompt = (
                f"{time_info}"
                "Ты — близкий друг и крутой ИИ-помощник Алексея. Твой стиль общения — живой, "
                "свободный, с юмором и иронией, как в реальном разговоре. Никакой официальщины, "
                "никаких фраз 'Чем могу быть полезен' или 'Как я могу помочь'. "
                "Отвечай всегда только на русском языке, просто, емко и по-человечески. "
                "Старайся писать коротко и по делу, не расписывай длинные простыни текста, "
                "если только Алексей сам не попросит ответить детально или развернуто. "
                f"{web_search_instruction}\n"
                "Если Алексей просит шутку — шути смешно, жизненно, избегай избитых шаблонов."
            )

        # 2. ЗАПИСЬ В БД ТОЛЬКО ДЛЯ ЛИЧНОГО РЕЖИМА АЛЕКСЕЯ
        conn = None
        if mode != "public":
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO chat_messages (role, content) VALUES (%s, %s)",
                        ("user", user_message)
                    )
                    conn.commit()
                except Exception as e:
                    logger.error(f"Не удалось записать сообщение пользователя: {e}")

        # 3. СБОР КОНТЕКСТА ИСТОРИИ
        messages_for_ai = [{"role": "system", "content": system_prompt}]
        
        if mode == "public":
            for msg in client_history[:-1]:
                clean_content = re.sub(r"^\[Системное инфо\..*?\]\s*", "", msg.get("content") or "", flags=re.DOTALL).strip()
                messages_for_ai.append({"role": msg.get("role"), "content": clean_content})
        else:
            history_messages = []
            if conn:
                try:
                    cur.execute("""
                        SELECT role, content 
                        FROM chat_messages 
                        WHERE id < (SELECT MAX(id) FROM chat_messages)
                        ORDER BY id DESC 
                        LIMIT 10
                    """)
                    rows = cur.fetchall()
                    for row in rows[::-1]:
                        history_messages.append({"role": row[0], "content": row[1]})
                except Exception as e:
                    logger.error(f"Не удалось достать контекст для ИИ: {e}")
            messages_for_ai.extend(history_messages)

        # Формируем текущее сообщение (с поддержкой фото, если есть)
        current_content = [{"type": "text", "text": user_message}]
        if image_base64:
            current_content.append({"type": "image_url", "image_url": {"url": image_base64}})
            
        messages_for_ai.append({"role": "user", "content": current_content})

        # 4. ЗАПРОС К OPENROUTER С АВТОМАТИЧЕСКИМ ПЕРЕБОРОМ НАШЕГО СПИСКА
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        reply = None
        last_error_details = "Все модели вернули ошибку"
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {api_key}"}
            
            for current_model in FREE_MODELS:
                try:
                    logger.info(f"Пробуем отправить запрос в модель: {current_model}")
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json={
                            "model": current_model, 
                            "messages": messages_for_ai,
                            "max_tokens": 400
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code != 200:
                        last_error_details = f"Модель {current_model} вернула статус {response.status_code}: {response.text}"
                        continue
                        
                    resp_json = response.json()
                    
                    if "error" in resp_json:
                        last_error_details = f"Внутренняя ошибка на {current_model}: {resp_json['error']}"
                        continue
                        
                    reply = resp_json['choices'][0]['message']['content']
                    break
                        
                except Exception as model_err:
                    last_error_details = f"Сбой сети на {current_model}: {str(model_err)}"
                    continue

            # Если перебрали абсолютно всё и глухо
            if reply is None:
                if conn:
                    cur.close()
                    conn.close()
                return {"text": f"Сбой перебора бесплатных моделей. Последняя ошибка: {last_error_details}"}
                
            # ОТВЕТ ПИШЕМ В БД ТОЛЬКО ДЛЯ АЛЕКСЕЯ
            if mode != "public" and conn:
                try:
                    cur.execute(
                        "INSERT INTO chat_messages (role, content) VALUES (%s, %s)",
                        ("assistant", reply)
                    )
                    conn.commit()
                except Exception as e:
                    logger.error(f"Не удалось записать ответ ИИ: {e}")
            
            if conn:
                cur.close()
                conn.close()

            return {"text": reply}
                
    except Exception as e:
        return {"text": f"Ошибка бэкенда: {str(e)}"}

@app.get("/api/history")
async def get_history():
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor() 
        cur.execute("""
            SELECT id, role, content 
            FROM chat_messages 
            ORDER BY id DESC 
            LIMIT 15
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        if not rows:
            return []
            
        history_summary = []
        for row in rows[::-1]:
            history_summary.append({"id": row[0], "role": row[1], "content": row[2]})
            
        return history_summary
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории: {e}")
        return []

@app.delete("/api/delete/{msg_id}")
async def delete_message(msg_id: int):
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "message": "Нет подключения к БД"}
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_messages WHERE id = %s", (msg_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "message": f"Сообщение {msg_id} удалено"}
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения {msg_id}: {e}")
        return {"status": "error", "message": str(e)}
