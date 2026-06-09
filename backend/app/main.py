import os
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Теперь мы берем адрес базы данных из настроек Render
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Создание таблиц
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Привет! Бот успешно подключен к базе данных."}
    
