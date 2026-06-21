import os
import httpx
import logging
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url: return None
    try:
        return psycopg2.connect(db_url, connect_timeout=3)
    except Exception as e:
        logger.error(f"БД ошибка: {e}")
        return None

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    raw_user_message = data.get("text") or ""
    mode = data.get("mode") or "private"
    
    user_message = re.sub(r"^\[Системное инфо\..*?\]\s*", "", raw_user_message, flags=re.DOTALL).strip()
    
    # Конфигурация Groq
    groq_key = os.environ.get("GROG_KEY")
    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    
    # Формируем запрос для Groq (используем модель llama-3.3-70b-versatile)
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Ты — крутой помощник Алексея. Отвечай кратко, по-человечески, с юмором, на русском языке."},
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(groq_url, headers=headers, json=payload, timeout=20.0)
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
            else:
                reply = f"Ошибка Groq: {response.status_code} - {response.text}"
        except Exception as e:
            reply = f"Ошибка подключения: {str(e)}"
            
    return {"text": reply}

@app.get("/api/history")
async def get_history():
    return [] # История пока отключена для простоты

@app.delete("/api/delete/{msg_id}")
async def delete_message(msg_id: int):
    return {"status": "success"}
