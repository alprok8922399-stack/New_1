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
    query = users.
