import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Настройка базы данных
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Настройка CORS (разрешаем запросы с любого сайта)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создание таблиц
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Привет! Бот успешно подключен к базе данных."}

@app.post("/api/chat")
def chat_endpoint(data: dict):
    user_message = data.get("message")
    return {"reply": f"Вы сказали: {user_message}"}
    
