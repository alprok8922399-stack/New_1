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

async def ask_llm(messages):
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

    return "Извини, я сейчас не могу ответить (API не настроены или недоступны)."

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    raw_text = data.get("text") or ""
    mode = data.get("mode") or "public"
    user_name = data.get("user") or "Гость"
    client_time = data.get("client_time") or "Неизвестно"
    
    # Собираем историю для передачи боту
    history_messages = []
    
    # Если режим приватный, подтягиваем последние 9 сообщений из базы (чтобы вместе с новым было 10)
    if mode == "private":
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT role, content FROM chat_messages ORDER BY id DESC LIMIT 9")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            # Разворачиваем, чтобы хронология была правильной (от старых к новым)
            for r in rows[::-1]:
                history_messages.append({"role": r[0], "role" if r[0]=='user' else 'assistant': r[0], "content": r[1]})

    # Добавляем системную инструкцию в самое начало
    system_prompt = f"Ты — друг и помощник. Пользователя зовут {user_name}. Текущие дата и время на устройстве пользователя: {client_time}."
    
    # Формируем итоговый пакет для ИИ: Системник -> История из БД -> Новое сообщение
    full_messages = [{"role": "system", "content": system_prompt}]
    
    for msg in history_messages:
        # Приводим к строгому формату user/assistant
        role = "user" if msg["role"] == "user" else "assistant"
        full_messages.append({"role": role, "content": msg["content"]})
        
    full_messages.append({"role": "user", "content": raw_text})
    
    # Отправляем боту ВСЮ цепочку разговора
    reply = await ask_llm(full_messages)

    # Сохраняем новую реплику в базу ТОЛЬКО если приватный режим
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
    if mode == "public":
        return []
    
    conn = get_db_connection()
    if not conn: return []
    cur = conn.cursor()
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
