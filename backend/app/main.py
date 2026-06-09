import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# Импортируем ваш клиент
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

@app.get("/")
def read_root():
    return {"message": "Бэкенд запущен!"}

@app.post("/api/chat")
async def chat_endpoint(data: dict):
    # Теперь мы ищем поле 'text', как присылает фронтенд
    user_message = data.get("text")
    
    if not user_message:
        return {"text": "Ошибка: пустое сообщение"}
    
    try:
        # Отправляем в ваш openai_client
        reply = await create_completion(user_message)
        return {"text": reply}
    except Exception as e:
        return {"text": f"Ошибка ИИ: {str(e)}"}
        
