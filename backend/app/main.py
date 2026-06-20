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
        
        # Очищаем текст сообщения от системного мусора [Системное инфо...]
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

        # 3. СБОР КОНТЕКСТА И ИСТОРИИ ДЛЯ GOOGLE GEMINI
        gemini_contents = [{"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]}]
        gemini_contents.append({"role": "model", "parts": [{"text": "Понял тебя. Инструкции приняты. Буду общаться строго по этим правилам."}]})
        
        if mode == "public":
            for msg in client_history[:-1]:
                clean_content = re.sub(r"^\[Системное инфо\..*?\]\s*", "", msg.get("content") or "", flags=re.DOTALL).strip()
                g_role = "user" if msg.get("role") == "user" else "model"
                gemini_contents.append({"role": g_role, "parts": [{"text": clean_content}]})
        else:
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
                        g_role = "user" if row[0] == "user" else "model"
                        gemini_contents.append({"role": g_role, "parts": [{"text": row[1]}]})
                except Exception as e:
                    logger.error(f"Не удалось достать контекст для ИИ: {e}")

        # Добавляем текущее сообщение пользователя
        user_parts = [{"text": user_message}]
        
        # Если есть фото
        if image_base64 and "," in image_base64:
            try:
                mime_type, b64_data = image_base64.split(",", 1)
                mime_type = mime_type.replace("data:", "").replace(";base64", "")
                user_parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64_data
                    }
                })
            except Exception as img_err:
                logger.error(f"Ошибка обработки фото для Gemini: {img_err}")

        gemini_contents.append({"role": "user", "parts": user_parts})

        # 4. ЗАПРОС К GOOGLE GEMINI API С ПОДКЛЮЧЕННЫМ ИНТЕРНЕТ-ПОИСКОМ
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        reply = "Не удалось получить ответ от Google Gemini."
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        
        # Формируем тело запроса и активируем официальный инструмент Google Поиска
        payload = {
            "contents": gemini_contents,
            "tools": [{"google_search": {}}]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    gemini_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=20.0  # Увеличили таймаут, так как ИИ теперь тратит время на поиск в сети
                )
                
                if response.status_code == 200:
                    resp_json = response.json()
                    candidates = resp_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            reply = parts[0].get("text", "")
                else:
                    reply = f"Ошибка Gemini API (Статус {response.status_code}): {response.text}"
            except Exception as gemini_err:
                reply = f"Сбой сети при JSON-запросе к Gemini: {str(gemini_err)}"

        # ОТВЕТ ПИШЕМ В БД ТОЛЬКО ДЛЯ АЛЕКСЕЯ
        if mode != "public" and conn and not reply.startswith("Ошибка Gemini") and not reply.startswith("Сбой сети"):
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
