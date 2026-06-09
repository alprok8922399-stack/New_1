import os
import datetime
import httpx
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Настройки базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель базы данных для сообщений
class DBMessage(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, index=True)  # "user" или "bot"
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)

# Инициализация FastAPI
app = FastAPI(title="AI Chat API")

# Настройка CORS, чтобы фронтенд мог слать запросы
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Схемы данных для API
class MessageCreate(BaseModel):
    text: str

class MessageResponse(BaseModel):
    id: int
    sender: str
    text: str
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

# Настройки OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"

@app.get("/")
def read_root():
    return {"status": "working", "message": "Backend is running"}

@app.post("/api/chat", response_model=MessageResponse)
async def chat_endpoint(payload: MessageCreate, db: Session = Depends(get_db)):
    user_text = payload.text
    
    if not user_text.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # 1. Сохраняем сообщение пользователя в базу
    db_user_msg = DBMessage(sender="user", text=user_text)
    db.add(db_user_msg)
    db.commit()
    db.refresh(db_user_msg)

    # 2. Получаем историю (последние 10 сообщений) для контекста
    history = db.query(DBMessage).order_by(DBMessage.timestamp.desc()).limit(10).all()
    history.reverse()

    # Формируем сообщения для ИИ
    messages_for_ai = []
    for msg in history:
        role = "user" if msg.sender == "user" else "assistant"
        messages_for_ai.append({"role": role, "content": msg.text})

    if not messages_for_ai:
        messages_for_ai.append({"role": "user", "content": user_text})

    # 3. Запрос к OpenRouter (DeepSeek)
    if not OPENROUTER_API_KEY:
        bot_response_text = "[Ошибка конфигурации: API ключ OpenRouter не задан]: " + user_text
    else:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://render.com",
            "X-Title": "AI Chat Project"
        }
        
        data = {
            "model": MODEL_NAME,
            "messages": messages_for_ai
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(OPENROUTER_URL, headers=headers, json=data, timeout=30.0)
                if response.status_code == 200:
                    result = response.json()
                    bot_response_text = result['choices'][0]['message']['content']
                else:
                    bot_response_text = f"[Ошибка OpenRouter API: Статус {response.status_code}]"
            except Exception as e:
                bot_response_text = f"[Ошибка сети при запросе к ИИ: {str(e)}]"

    # 4. Сохраняем ответ бота в базу
    db_bot_msg = DBMessage(sender="bot", text=bot_response_text)
    db.add(db_bot_msg)
    db.commit()
    db.refresh(db_bot_msg)

    return db_bot_msg
