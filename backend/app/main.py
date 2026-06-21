import os
import httpx
import logging
import re
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

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    raw_user_message = data.get("text") or ""
    user_name = data.get("user") or "Гость"
    mode = data.get("mode") or "public"
    
    # Запись в БД: сохраняем сообщение с префиксом имени, чтобы потом найти его
    conn = get_db_connection()
    if conn and mode != "public":
        cur = conn.cursor()
        cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", 
                    ("user", f"[{user_name}]: {raw_user_message}"))
        conn.commit()
        cur.close()

    system_instruction = f"Ты — друг. Пользователя зовут {user_name}."

    groq_key = os.environ.get("GROG_KEY")
    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": raw_user_message}]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(groq_url, headers=headers, json=payload, timeout=20.0)
        reply = response.json()['choices'][0]['message']['content'] if response.status_code == 200 else "Ошибка"

    if conn and mode != "public":
        cur = conn.cursor()
        cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("assistant", reply))
        conn.commit()
        cur.close()
        conn.close()
            
    return {"text": reply}

@app.get("/api/history")
async def get_history(user: str = "Гость"):
    conn = get_db_connection()
    if not conn: return []
    cur = conn.cursor()
    # Ищем сообщения, которые начинаются с [Имя пользователя] или являются ответами бота
    query = "SELECT id, role, content FROM chat_messages WHERE content LIKE %s OR role = 'assistant' ORDER BY id DESC LIMIT 20"
    cur.execute(query, (f"[{user}%",))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "role": r[1], "content": r[2].replace(f"[{user}]: ", "") if r[1] == 'user' else r[2]} for r in rows[::-1]]

@app.delete("/api/delete/{msg_id}")
async def delete_message(msg_id: int):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_messages WHERE id = %s", (msg_id,))
        conn.commit()
        cur.close()
        conn.close()
    return {"status": "success"}
