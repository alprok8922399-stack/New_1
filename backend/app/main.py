import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
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

@app.post("/api/chat")
async def chat_endpoint(data: dict):
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        user = User(name="Друг")
        db.add(user)
        db.commit()
        db.refresh(user)

    user_message = data.get("text", "").strip()
    
    # Сохраняем сообщение пользователя
    msg = Message(role="user", content=user_message, user_id=user.id)
    db.add(msg)
    db.commit()

    # ПРОВЕРКА ИМЕНИ
    if user_message.lower().startswith("меня зовут "):
        name_part = user_message.split(" ", 2)[2].strip()
        user.name = name_part
        db.commit()
        reply_text = f"Запомнил! Теперь тебя зовут {name_part}."
    elif user_message.lower() in ["как меня зовут?", "как меня зовут"]:
        reply_text = f"Тебя зовут {user.name}."
    else:
        reply_text = await create_completion(f"Пользователя зовут {user.name}. Его сообщение: {user_message}")

    # Сохраняем ответ бота
    bot_msg = Message(role="assistant", content=reply_text, user_id=user.id)
    db.add(bot_msg)
    db.commit()
    db.close()
    
    return {"text": reply_text}
