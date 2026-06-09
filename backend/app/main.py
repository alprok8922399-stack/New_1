from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Настройка базы данных
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname" 

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Создание таблиц
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Привет! Бот запущен и работает."}
    
