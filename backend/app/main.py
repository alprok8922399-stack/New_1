import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.openai_client import create_completion

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/api/chat")
async def chat_endpoint(data: dict):
    db = SessionLocal()
    user = db.query(User).first()
    user_message = data.get("text", "").strip()

    # СТРОГАЯ ПРОВЕРКА ИМЕНИ
    if user_message.lower().startswith("меня зовут "):
        name_part = user_message.split(" ", 2)[2].strip()
        if not user:
            user = User(name=name_part)
            db.add(user)
        else:
            user.name = name_part
        db.commit()
        db.close()
        return {"text": f"Запомнил! Теперь тебя зовут {name_part}."}

    # ПРОВЕРКА ВОПРОСА О ИМЕНИ
    if user_message.lower() in ["как меня зовут?", "как меня зовут"]:
        db.close()
        return {"text": f"Тебя зовут {user.name if user else 'Друг'}."}

    # ОБЫЧНЫЙ ОТВЕТ
    user_name = user.name if user else "Друг"
    reply = await create_completion(f"Пользователя зовут {user_name}. Его сообщение: {user_message}")
    db.close()
    return {"text": reply}
    
