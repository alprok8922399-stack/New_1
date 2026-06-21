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
    mode = data.get("mode") or "private"
    user_name = data.get("user") or "Гость"
    user_message = re.sub(r"^\[Системное инфо\..*?\]\s*", "", raw_user_message, flags=re.DOTALL).strip()
    
    # Запись пользователя в БД с именем
    conn = get_db_connection()
    if conn and mode != "public":
        cur = conn.cursor()
        # ВНИМАНИЕ: Если таблица не менялась, этот код может вызвать ошибку.
        # Если будет ошибка, просто замени имя колонки content на комбинацию с именем.
        cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("user", f"[{user_name}]: {user_message}"))
        conn.commit()
        cur.close()

    system_instruction = (
        f"Ты — близкий друг и ИИ-помощник. Пользователя зовут {user_name}. "
        "Стиль общения: живой, с юмором, без официальщины."
    )

    groq_key = os.environ.get("GROG_KEY")
    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_message}]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(groq_url, headers=headers, json=payload, timeout=20.0)
        reply = response.json()['choices'][0]['message']['content'] if response.status_code == 200 else "Ошибка Groq"

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
    # Берем последние 15 записей
    cur.execute("SELECT id, role, content FROM chat_messages ORDER BY id DESC LIMIT 15")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "role": r[1], "content": r[2]} for r in rows[::-1]]

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
