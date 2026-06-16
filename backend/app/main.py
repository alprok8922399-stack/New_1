import os
import httpx
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

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

# Лимит символов для одного сообщения (защита от огромных текстов)
MAX_USER_MESSAGE_LENGTH = 8000

# Подключение к БД
def get_db_connection():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

# Инициализация таблицы при старте
@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            role VARCHAR(20),
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message", "")

        if len(user_message) > MAX_USER_MESSAGE_LENGTH:
            return {"error": "Сообщение слишком длинное"}

        # Сохраняем сообщение пользователя в БД
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_messages (role, content) VALUES (%s, %s)",
            ("user", user_message)
        )
        conn.commit()
        cur.close()
        conn.close()

        # Здесь будет запрос к OpenRouter
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": user_message}]
                }
            )
            ai_response = response.json()["choices"][0]["message"]["content"]

        # Сохраняем ответ ИИ в БД
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_messages (role, content) VALUES (%s, %s)",
            ("assistant", ai_response)
        )
        conn.commit()
        cur.close()
        conn.close()

        return {"response": ai_response}

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return {"error": "Произошла ошибка"}
        
