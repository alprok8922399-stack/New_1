import os
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

# Получаем ссылку на БД
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Создаем движок (базу мы уже сбросили, теперь просто работаем с ней)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

# Модель пользователя
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    secret_phrase = Column(String, unique=True, index=True)
    name = Column(String, default="Друг")

# Создаем таблицы, если их нет
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

        # Проверяем пользователя в базе
        user = db.query(User).filter(User.secret_phrase == secret).first()
        if not user:
            user = User(secret_phrase=secret, name="Пользователь")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # --- ПОДКЛЮЧАЕМ НАСТОЯЩИЙ ИИ ЧЕРЕЗ OPENROUTER ---
        api_key = os.environ.get("OPENROUTER_API_KEY", "ПОДСТАВЬ_СВОЙ_КЛЮЧ_ЕСЛИ_НЕТ_В_НАСТРОЙКАХ")
        
        # Делаем запрос к бесплатной модели ИИ
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemma-2-9b-it:free", # Хорошая бесплатная модель ИИ
                    "messages": [
                        {"role": "system", "content": f"Ты вежливый ИИ-ассистент. Собеседника зовут {user.name}."},
                        {"role": "user", "content": user_message}
                    ]
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result['choices'][0]['message']['content']
            else:
                reply = f"Ошибка ИИ (Код {response.status_code}): Не удалось получить ответ от нейросети."

        return {"text": reply}
        
    except Exception as e:
        return {"text": f"Ошибка бэкенда: {str(e)}"}
    finally:
        db.close()
