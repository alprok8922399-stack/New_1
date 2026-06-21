import os
import httpx
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

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

async def ask_llm(messages, mode):
    # 1. Попытка Groq
    groq_key = os.environ.get("GROG_KEY")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://api.groq.com/openai/v1/chat/completions", 
                                     headers={"Authorization": f"Bearer {groq_key}"},
                                     json={"model": "llama-3.3-70b-versatile", "messages": messages}, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
    except Exception:
        pass

    # 2. Попытка Gemini (здесь нужно будет добавить твой ключ)
    # 3. Попытка OpenRouter (здесь нужно будет добавить твой ключ)
    return "Извини, я сейчас не могу ответить (API не настроены или недоступны)."

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    raw_text = data.get("text") or ""
    mode = data.get("mode") or "public"
    user_name = "Алексей"
    
    # Системная инструкция
    messages = [{"role": "system", "content": f"Ты — друг и помощник. Пользователя зовут {user_name}."}, {"role": "user", "content": raw_text}]
    
    reply = await ask_llm(messages, mode)

    # Сохраняем в базу ТОЛЬКО если приватный режим
    if mode == "private":
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("user", raw_text))
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("assistant", reply))
            conn.commit()
            cur.close()
            conn.close()
            
    return {"text": reply}

@app.get("/api/history")
async def get_history(mode: str = "public"):
    # Если публичный режим — истории нет
    if mode == "public":
        return []
    
    conn = get_db_connection()
    if not conn: return []
    cur = conn.cursor()
    # Берем последние 10 записей
    cur.execute("SELECT id, role, content FROM chat_messages ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "role": r[1], "content": r[2]} for r in rows[::-1]]

@app.get("/api/clear")
async def clear_chat():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_messages")
        conn.commit()
        cur.close()
        conn.close()
    return {"status": "cleared"}
