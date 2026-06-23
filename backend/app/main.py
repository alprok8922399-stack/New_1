import os
import httpx
import logging
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

# Класс для приветствия
class Greeting:
    def __init__(self, name):
        self.name = name

    def get_greeting(self):
        return f"Привет, {self.name}! Как у тебя дела сегодня?"

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
    user_image = data.get("image") or ""  # Получаем картинку в формате Base64
    
    # Извлечение системной инфы
    time_match = re.search(r"Текущие дата и время:\s*([^\]]+)", raw_user_message)
    client_time = time_match.group(1).strip() if time_match else "Неизвестно"
    name_match = re.search(r"Имя собеседника:\s*([^\]]+)", raw_user_message)
    user_name = name_match.group(1).strip() if name_match else "Алексей"

    user_message = re.sub(r"^\[Системное инфо.*?\]\s*", "", raw_user_message, flags=re.DOTALL).strip()
    
    # Ключи из твоих настроек
    groq_key = os.environ.get("GROQ_KEY") or os.environ.get("GROG_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    or_key = os.environ.get("OPENROUTER_API_KEY")
    
    # История из БД
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

    system_prompt = f"Ты — friend and helper. Пользователя зовут {user_name}. Текущие дата и время: {client_time}. Отвечай кратко, с юмором, на русском. Если передана картинка или скриншот, внимательно изучи её и помоги пользователю."
    
    full_messages = [{"role": "system", "content": system_prompt}]
    
    if not history_messages and mode == "private":
        greeter = Greeting(user_name)
        full_messages.append({"role": "assistant", "content": greeter.get_greeting()})
    
    for msg in history_messages:
        full_messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Формируем последнее сообщение пользователя в зависимости от наличия картинки
    if user_image:
        # Для OpenRouter/Gemini с картинкой нужен специальный формат структуры контента
        user_content = [
            {"type": "text", "text": user_message if user_message else "Посмотри на этот скриншот"},
            {"type": "image_url", "image_url": {"url": user_image}}
        ]
    else:
        user_content = user_message

    full_messages.append({"role": "user", "content": user_content})
    
    reply = "Ошибка: все сервисы недоступны"
    
    async with httpx.AsyncClient() as client:
        # 1. Первая попытка: GROQ (Только если НЕТ картинки, так как Groq не умеет в зрение)
        if groq_key and not user_image:
            try:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={"model": "llama-3.3-70b-versatile", "messages": full_messages},
                    timeout=30.0
                )
                if response.status_code == 200:
                    reply = response.json()['choices'][0]['message']['content']
            except: pass

        # 2. Вторая попытка: НАДЕЖНЫЙ OPENROUTER (Сюда идем сразу, если ЕСТЬ картинка, или если Groq упал)
        if (reply.startswith("Ошибка") or "Ошибка" in reply) and or_key:
            # Для картинок в OpenRouter используем универсальную зрячую модель от Google
            model_to_use = "google/gemini-2.5-flash" if user_image else "meta-llama/llama-3.3-70b-instruct"
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                    json={"model": model_to_use, "messages": full_messages},
                    timeout=30.0
                )
                if response.status_code == 200:
                    reply = response.json()['choices'][0]['message']['content']
            except: pass

        # 3. Третья попытка: ЗАПАСНОЙ БЕСПЛАТНЫЙ GEMINI (Если OpenRouter тоже не ответил)
        if (reply.startswith("Ошибка") or "Ошибка" in reply) and gemini_key:
            try:
                response = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    headers={"Authorization": f"Bearer {gemini_key}", "Content-Type": "application/json"},
                    json={"model": "gemini-1.5-flash", "messages": full_messages},
                    timeout=30.0
                )
                if response.status_code == 200:
                    reply = response.json()['choices'][0]['message']['content']
            except: pass
            
    # Сохраняем в БД (только текст, саму тяжелую картинку в историю базы не пишем)
    if mode == "private" and not reply.startswith("Ошибка"):
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("user", user_message if user_message else "Отправлен скриншот"))
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
