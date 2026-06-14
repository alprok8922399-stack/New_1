import os
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

# Получаем ссылку на БД
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Создаем движок
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

# Модель пользователя
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    secret_phrase = Column(String, unique=True, index=True)
    name = Column(String, default="Друг")

# НАДЁЖНЫЙ КАСКАДНЫЙ СБРОС ТАБЛИЦ ПЕРЕД ЗАПУСКОМ
with engine.connect() as connection:
    # Эта команда силой удаляет таблицы users и messages, игнорируя старые связи
    connection.execute(text("DROP TABLE IF EXISTS messages CASCADE;"))
    connection.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
    connection.commit()

# Теперь создаем чистые, правильные таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    db = db_session()
    try:
        data = await request.json()
        secret = data.get("secret", "test-secret")
        user_message = data.get("text", "")

        # Ищем пользователя по новой колонке secret_phrase
        user = db.query(User).filter(User.secret_phrase == secret).first()
        if not user:
            user = User(secret_phrase=secret, name="Пользователь")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        reply = f"Привет, {user.name}! База данных полностью очищена и теперь работает без ошибок!"
        return {"text": reply}
    except Exception as e:
        return {"text": f"Ошибка БД: {str(e)}"}
    finally:
        db.close()
