import os
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Настройка базы данных с исправлением старого формата Render
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")

# ЕСЛИ РЕНДЕР ДАЛ ССЫЛКУ С postgres://, МЕНЯЕМ ЕЁ НА postgresql:// ДЛЯ SQLALCHEMY 2.0
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модели данных
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    secret_phrase = Column(String, unique=True, index=True)
    name = Column(String, default="Друг")
    messages = relationship("Message", back_populates="user")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)
    content = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="messages")

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI()

# НАСТРОЙКА CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    db = SessionLocal()
    try:
        body_bytes = await request.body()
        data = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        data = {}

    secret = data.get("secret", "test-secret")
    
    # Авто-создание пользователя
    user = db.query(User).filter(User.secret_phrase == secret).first()
    if not user:
        user = User(secret_phrase=secret, name="Пользователь")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Сохраняем сообщение пользователя
    user_message = data.get("text", "").strip()
    msg = Message(role="user", content=user_message, user_id=user.id)
    db.add(msg)
    db.commit()
    
    # Ответ бота
    reply_text = f"Привет, {user.name}! Твой бэкенд наконец-то ожил и база данных работает!"
    
    bot_msg = Message(role="assistant", content=reply_text, user_id=user.id)
    db.add(bot_msg)
    db.commit()
    
    db.close()
    
    return {"text": reply_text}
