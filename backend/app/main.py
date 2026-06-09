import os
import datetime
import json
import urllib.request
import urllib.error
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
    sender = Column(String, index=True)
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Инициализация FastAPI
app = FastAPI(title="AI Chat API")

# Максимально разрешающий CORS (чтобы браузеры не блокировали запросы с фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
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

# API Эндпоинт для чата
@app.post("/api/chat", response_model=MessageResponse)
async def chat_endpoint(payload: MessageCreate, db: Session = Depends(get_db)):
    user_text = payload.text
    
    if not user_text.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    db_user_msg = DBMessage(sender="user", text=user_text)
    db.add(db_user_msg)
    db.commit()
    db.refresh(db_user_msg)

    history = db.query(DBMessage).order_by(DBMessage.timestamp.desc()).limit(10).all()
    history.reverse()

    messages_for_ai = []
    for msg in history:
        role = "user" if msg.sender == "user" else "assistant"
        messages_for_ai.append({"role": role, "content": msg.text})

    if not messages_for_ai:
        messages_for_ai.append({"role": "user", "content": user_text})

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

        req_body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(OPENROUTER_URL, data=req_body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_status = response.getcode()
                if res_status == 200:
                    res_data = json.loads(response.read().decode("utf-8"))
                    bot_response_text = res_data['choices'][0]['message']['content']
                else:
                    bot_response_text = f"[Ошибка OpenRouter API: Статус {res_status}]"
        except urllib.error.HTTPError as e:
            bot_response_text = f"[Ошибка OpenRouter HTTP: {e.code} {e.reason}]"
        except Exception as e:
            bot_response_text = f"[Ошибка сети при запросе к ИИ: {str(e)}]"

    db_bot_msg = DBMessage(sender="bot", text=bot_response_text)
    db.add(db_bot_msg)
    db.commit()
    db.refresh(db_bot_msg)

    return db_bot_msg

# Подключение статических файлов фронтенда
frontend_path = "/app/frontend" if os.path.exists("/app/frontend") else "frontend"

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str):
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "index.html not found"}
else:
    @app.get("/")
    def read_root():
        return {"status": "working", "message": "Backend is running"}
