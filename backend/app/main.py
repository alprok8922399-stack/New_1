from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import databases
import sqlalchemy
import openai
import os
import uuid
from datetime import datetime
from .database import messages, database  # ← импорты из database.py

app = FastAPI()

# 🔥 CORS (разрешаем фронтенд)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat-ai-frontend-y1bt.onrender.com", "http://localhost"],  # ✅
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Класс для запроса
class ChatRequest(BaseModel):
    message: str
    user_secret: str  # Будем проверять пользователя позже

# Подключение к базе
@app.on_event("startup")
async def startup():
    await database.connect()

# Отключение от базы
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Основной эндпоинт
@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        # Проверка пользователя (пока заглушка)
        if False:  # Позже заменим на проверку secret_phrase
            raise ValueError("Доступ закрыт!")

        # Готовим сообщение
        timestamp = datetime.now()
        role = "user"
        content = req.message

        # Сохраняем в базу
        query = messages.insert().values(role=role, content=content, timestamp=timestamp)
        await database.execute(query)

        # Формируем массив для OpenAI
        history = [
            {"role": "system", "content": "Ты помощник"},
            {"role": "user", "content": content},
        ]

        # Отправляем в модель
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=history,
            temperature=0.7,
            max_tokens=2000,
        )

        # Сохраняем ответ ИИ
        bot_response = response.choices[0].message.content
        query = messages.insert().values(
            role="bot", content=bot_response, timestamp=datetime.now()
        )
        await database.execute(query)

        return {"response": bot_response}

    except Exception as e:
        return {"error": str(e)}
