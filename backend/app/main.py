import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ВРЕМЕННАЯ КОМАНДА ДЛЯ УДАЛЕНИЯ ТАБЛИЦЫ
@app.get("/reset-table")
async def reset_table():
    db = SessionLocal()
    db.execute(text("DROP TABLE IF EXISTS messages CASCADE;"))
    db.commit()
    db.close()
    return {"message": "Таблица messages удалена. Теперь перезапустите или просто откройте чат."}

@app.post("/api/chat")
async def chat_endpoint(data: dict):
    secret = data.get("secret")
    db = SessionLocal()
    user = db.query(User).filter(User.secret_phrase == secret).first()
    
    if not user:
        db.close()
        return {"text": "Ошибка: неверный ключ доступа."}
    
    user_message = data.get("text", "").strip()
    msg = Message(role="user", content=user_message, user_id=user.id)
    db.add(msg)
    db.commit()
    
    reply_text = f"Привет, {user.name}. Ты прислал: {user_message}"
    
    bot_msg = Message(role="assistant", content=reply_text, user_id=user.id)
    db.add(bot_msg)
    db.commit()
    db.close()
    
    return {"text": reply_text}
