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
    return psycopg2.connect(db_url, connect_timeout=3) if db_url else None

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("text", "")
    
    system_prompt = (
        "Ты — ИИ-помощник по имени 'Друг и помощник!'. "
        "Если тебя спросят, как тебя зовут или кто ты, всегда отвечай: 'Друг и помощник!'. "
        "Твоя задача — общаться вежливо, на русском языке, делать красивые абзацы."
    )

    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("user", user_message))
            conn.commit()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "openrouter/auto", 
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            },
            timeout=30.0
        )
        reply = response.json()['choices'][0]['message']['content']
        
        if conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("assistant", reply))
                conn.commit()
                conn.close()
                
        return {"text": reply}

@app.get("/api/history")
async def get_history():
    conn = get_db_connection()
    if not conn: return []
    with conn.cursor() as cur:
        # ЗАБИРАЕМ 50 ПОСЛЕДНИХ СВЕЖИХ СООБЩЕНИЙ
        cur.execute("SELECT role, content FROM (SELECT id, role, content FROM chat_messages ORDER BY id DESC LIMIT 50) as sub ORDER BY id ASC")
        rows = cur.fetchall()
        conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]
