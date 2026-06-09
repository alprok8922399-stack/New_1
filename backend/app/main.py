import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.openai_client import create_completion

# Настройка базы данных
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# Хранилище: имя пользователя и история
user_name = "Друг"
chat_history = []

@app.get("/")
def read_root():
    return {"message": "Бэкенд запущен!"}

@app.post("/api/chat")
async def chat_endpoint(data: dict):
    global user_name
    user_message = data.get("text", "")
    
    # Если пользователь представляется
    if "меня зовут" in user_message.lower():
        user_name = user_message.split("зовут")[-1].strip()
        return {"text": f"Приятно познакомиться, {user_name}! Теперь я буду знать, как к тебе обращаться."}

    chat_history.append({"role": "user", "content": f"Меня зовут {user_name}. Мое сообщение: {user_message}"})
    
    if len(chat_history) > 10:
        chat_history.pop(0)
    
    try:
        reply = await create_completion(str(chat_history)) 
        chat_history.append({"role": "assistant", "content": reply})
        return {"text": reply}
    except Exception as e:
        return {"text": f"Ошибка ИИ: {str(e)}"}
        
