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

# Временное хранилище истории диалога
chat_history = []

@app.get("/")
def read_root():
    return {"message": "Бэкенд запущен!"}

@app.post("/api/chat")
async def chat_endpoint(data: dict):
    user_message = data.get("text")
    if not user_message:
        return {"text": "Ошибка: пустое сообщение"}
    
    # Добавляем сообщение пользователя в историю
    chat_history.append({"role": "user", "content": user_message})
    
    # Ограничиваем историю последними 10 сообщениями, чтобы не перегружать ИИ
    if len(chat_history) > 10:
        chat_history.pop(0)
    
    try:
        # Отправляем всю историю в ИИ
        # Примечание: в openai_client.py нужно будет тоже передавать список
        reply = await create_completion(str(chat_history)) 
        
        # Добавляем ответ бота в историю
        chat_history.append({"role": "assistant", "content": reply})
        
        return {"text": reply}
    except Exception as e:
        return {"text": f"Ошибка ИИ: {str(e)}"}
        
