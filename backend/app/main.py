import os
import httpx
import logging
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
            # Таблицу больше не удаляем, она уже создана правильно!
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
        user_message = data.get("text") or ""
        image_base64 = data.get("image") or ""
        
        system_prompt = "Ты — полезный, вежливый и умный ИИ-помощник. Отвечай всегда подробно, развернуто и только на русском языке."

        # Сохраняем новое сообщение пользователя в базу данных ГЛАВНОГО чата
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

        # СОБИРАЕМ ИСТОРИЮ ДЛЯ ИИ: Достаем последние 10 сообщений ПЕРЕД текущим запросом
        history_messages = []
        if conn:
            try:
                # Берем последние 10 записей, но исключаем только что добавленное сообщение пользователя,
                # чтобы не дублировать его (мы добавим его в самом конце как контент с картинкой)
                cur.execute("""
                    SELECT role, content 
                    FROM chat_messages 
                    WHERE id < (SELECT MAX(id) FROM chat_messages)
                    ORDER BY id DESC 
                    LIMIT 10
                """)
                rows = cur.fetchall()
                
                # Переворачиваем, чтобы история шла от старых к новым
                for row in rows[::-1]:
                    history_messages.append({"role": row[0], "content": row[1]})
            except Exception as e:
                logger.error(f"Не удалось достать контекст для ИИ: {e}")

        # Формируем массив сообщений для OpenRouter
        messages_for_ai = [{"role": "system", "content": system_prompt}]
        
        # Добавляем прошлую историю (если она есть в базе)
        messages_for_ai.extend(history_messages)
        
        # Добавляем текущее сообщение пользователя (вместе с фото, если оно есть)
        current_content = [{"type": "text", "text": user_message}]
        if image_base64:
            current_content.append({"type": "image_url", "image_url": {"url": image_base64}})
            
        messages_for_ai.append({"role": "user", "content": current_content})

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        
        # Отправляем ИИ полную историю переписки!
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "openrouter/auto", 
                    "messages": messages_for_ai
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                
                # Сохраняем ответ ИИ в базу
                if conn:
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
            else:
                if conn:
                    cur.close()
                    conn.close()
                return {"text": f"Ошибка OpenRouter: {response.text}"}
                
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
            SELECT role, content 
            FROM chat_messages 
            ORDER BY id DESC 
            LIMIT 50
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        messages = []
        for row in rows:
            messages.append({
                "role": row[0],
                "text": row[1]
            })
            
        return messages[::-1]
    except Exception as e:
        logger.error(f"Ошибка при получении истории: {e}")
        return []
