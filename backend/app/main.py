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
    
    # Извлекаем системную инфу (время, имя), если она есть
    client_time = "Неизвестно"
    user_name = "Алексей"
    
    time_match = re.search(r"Текущие дата и время:\s*([^.]+)", raw_user_message)
    if time_match:
        client_time = time_match.group(1).strip()
        
    name_match = re.search(r"Имя собеседника:\s*([^\]]+)", raw_user_message)
    if name_match:
        user_name = name_match.group(1).strip()

    # Чистим текст сообщения от системных тегов для отправки пользователю
    user_message = re.sub(r"^\[Системное инфо.*?\]\s*", "", raw_user_message, flags=re.DOTALL).strip()
    
    # Конфигурация Groq
    groq_key = os.environ.get("GROQ_KEY") or os.environ.get("GROG_KEY")
    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    
    # Собираем историю из БД, если режим приватный
    history_messages = []
    if mode == "private":
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT role, content FROM chat_messages ORDER BY id DESC LIMIT 9")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            for r in rows[::-1]:
                history_messages.append({"role": r[0], "content": r[1]})

    # Формируем системный промт с актуальным именем и временем
    system_prompt = f"Ты — friend and helper. Пользователя зовут {user_name}. Текущие дата и время на устройстве пользователя: {client_time}. Отвечай кратко, по-человечески, с юмором, на русском языке."
    
    full_messages = [{"role": "system", "content": system_prompt}]
    for msg in history_messages:
        full_messages.append({"role": msg["role"], "content": msg["content"]})
    full_messages.append({"role": "user", "content": user_message})
    
    # Формируем запрос для Groq
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": full_messages
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
            
    # Сохраняем новые сообщения в БД, если режим приватный
    if mode == "private" and not reply.startswith("Ошибка"):
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("user", user_message))
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("assistant", reply))
            conn.commit()
            cur.close()
            conn.close()
            
    return {"text": reply}

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
