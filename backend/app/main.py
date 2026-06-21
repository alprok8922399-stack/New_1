import os
import httpx
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

logging.basicConfig(level=logging.INFO)
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url: return None
    try: return psycopg2.connect(db_url, connect_timeout=3)
    except: return None

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_text = data.get("text", "").replace("[Системное инфо...]", "")
    image_data = data.get("image_data")
    mode = data.get("mode", "private")
    
    groq_key = os.environ.get("GROQ_KEY")
    or_key = os.environ.get("OPENROUTER_API_KEY")

    reply = "Ошибка: ключи не настроены"

    async with httpx.AsyncClient() as client:
        # ЕСЛИ ЕСТЬ КАРТИНКА -> OpenRouter (Vision)
        if image_data and or_key:
            try:
                payload = {
                    "model": "google/gemini-2.0-flash-exp",
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]}]
                }
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                    json=payload, timeout=60.0
                )
                if response.status_code == 200:
                    reply = response.json()['choices'][0]['message']['content']
                else:
                    reply = f"Ошибка OpenRouter: {response.status_code}"
            except Exception as e:
                reply = f"Исключение OpenRouter: {str(e)}"

        # ЕСЛИ ТОЛЬКО ТЕКСТ -> Groq (Быстро)
        elif groq_key:
            try:
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": user_text}]
                }
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json=payload, timeout=30.0
                )
                if response.status_code == 200:
                    reply = response.json()['choices'][0]['message']['content']
                else:
                    reply = f"Ошибка Groq: {response.status_code}"
            except Exception as e:
                reply = f"Исключение Groq: {str(e)}"

    # Сохранение в базу
    if not reply.startswith("Ошибка") and not reply.startswith("Исключение") and mode == "private":
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("user", user_text))
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("assistant", reply))
            conn.commit()
            cur.close()
            conn.close()
            
    return {"text": reply}

# (Функции history и delete оставь прежними)
@app.get("/api/history")
async def get_history():
    conn = get_db_connection()
    if not conn: return []
    cur = conn.cursor()
    cur.execute("SELECT id, role, content FROM chat_messages ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "role": r[1], "content": r[2]} for r in rows[::-1]]

@app.delete("/api/delete/{msg_id}")
async def delete_message(msg_id: int):
    conn = get_db_connection()
    if not conn: return {"status": "error"}
    cur = conn.cursor()
    cur.execute("DELETE FROM chat_messages WHERE id = %s", (msg_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}
