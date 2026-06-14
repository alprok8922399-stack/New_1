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

# Основной эндпоинт
@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        # ❗❗❗ Здесь будет логика привязки к admin
        pass

    except Exception as e:
        return {"error": str(e)}
