from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import databases
import sqlalchemy
import openai
import os
import uuid
from datetime import datetime
from .database import messages, database, users  # ← добавили users

app = FastAPI()

# 🔥 CORS (разрешаем фронтенд)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chat-ai-frontend-y1bt.onrender.com",
        "http://localhost",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Класс для запроса
class ChatRequest(BaseModel):
    message: str

# Подключение к базе
@app.on_event("startup")
async def startup():
    await database.connect()

    # ❗❗❗ Новый блок для загрузки админа
    query = users.select(users.c.username == "admin")
    existing = await database.fetch_one(query)

    if existing is None:
        now = datetime.utcnow()
        insert_query = users.insert().values(username="admin", created_at=now)
        await database.execute(insert_query)
        print("Админ успешно создан!")
    else:
        print("Админ уже есть.")

# Отключение от базы
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# === НОВЫЙ ЭНДПОИНТ ===
@app.get("/api/history")
async def get_history():
    """Возвращает последние 10 сообщений админа"""

    # Берем ID админа
    query = users.select(users.c.username == "admin")
    user_data = await database.fetch_one(query)
    user_id = user_data.id

    # Достаем историю
    query = (
        messages
        .select()
        .where(messages.c.user_id == user_id)
        .order_by(messages.c.timestamp.desc())
        .limit(10)
    )
    records = await database.fetch_all(query)

    # Преобразуем в удобный формат
    history = []
    for record in reversed(records):
        item = {
            "role": record.role,
            "content": record.content,
        }
        history.append(item)

    return history

# === ОСНОВНОЙ ЭНДПОИНТ ===
@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        # Получаем сообщение
        user_msg = req.message

        # ❗❗❗ Берем ID админа
        query = users.select(users.c.username == "admin")
        user_data = await database.fetch_one(query)
        user_id = user_data.id

        # Сохраняем сообщение пользователя
        now = datetime.utcnow()
        query = messages.insert().values(
            user_id=user_id,
            role="user",
            content=user_msg,
            timestamp=now
        )
        await database.execute(query)

        # Формируем полный контекст
        context = [
            {"role": "system", "content": "Ты помощник."},
            {"role": "user", "content": user_msg}
        ]

        # Получаем полную историю
        hist_query = (
            messages
            .select()
            .where(messages.c.user_id == user_id)
            .order_by(messages.c.timestamp.asc())
        )
        history = await database.fetch_all(hist_query)

        # Добавляем историю в контекст
        for rec in history:
            context.append({
                "role": rec.role,
                "content": rec.content
            })

        # Отправляем в модель
        OPENAI_API_KEY = os.getenv("OPENROUTER_API_KEY")
        openai.api_base = "https://api.openrouter.ai/v1"
        openai.api_key = OPENAI_API_KEY

        resp = openai.ChatCompletion.create(
            model="light-llama-2-70b-q4k-sft",
            messages=context,
            temperature=0.7,
            max_tokens=2000
        )

        # Сохраняем ответ ИИ
        bot_answer = resp.choices[0].message.content
        query = messages.insert().values(
            user_id=user_id,
            role="bot",
            content=bot_answer,
            timestamp=datetime.utcnow()
        )
        await database.execute(query)

        return {"response": bot_answer}

    except Exception as e:
        return {"error": str(e)}
