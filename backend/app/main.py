import os
import httpx
import logging
import re
import json
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
    user_image = data.get("image") or ""  # data:image/jpeg;base64,...
    
    # Извлечение системной инфы
    time_match = re.search(r"Текущие дата и время:\s*([^\]]+)", raw_user_message)
    client_time = time_match.group(1).strip() if time_match else "Неизвестно"
    name_match = re.search(r"Имя собеседника:\s*([^\]]+)", raw_user_message)
    user_name = name_match.group(1).strip() if name_match else "Алексей"

    user_message = re.sub(r"^\[Системное инфо.*?\]\s*", "", raw_user_message, flags=re.DOTALL).strip()
    
    # Ключи из настроек
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
    
    # Базовый текстовый формат истории (для Groq и стандартных запросов)
    text_messages = [{"role": "system", "content": system_prompt}]
    if not history_messages and mode == "private":
        greeter = Greeting(user_name)
        text_messages.append({"role": "assistant", "content": greeter.get_greeting()})
    for msg in history_messages:
        text_messages.append({"role": msg["role"], "content": msg["content"]})
    text_messages.append({"role": "user", "content": user_message if user_message else "Посмотри на этот скриншот"})
    
    reply = "Ошибка: все сервисы недоступны"
    
    async with httpx.AsyncClient() as client:
        
        # ЕСЛИ ЕСТЬ КАРТИНКА — ПРОБУЕМ ОБРАБОТАТЬ ЕЁ
        if user_image:
            # 1. Попытка через родной Gemini API (v1beta + ИСПРАВЛЕННАЯ МОДЕЛЬ gemini-2.5-flash)
            if gemini_key:
                try:
                    if "," in user_image:
                        img_data = user_image.split(",")[1]
                        mime_type = user_image.split(";")[0].replace("data:", "")
                    else:
                        img_data = user_image
                        mime_type = "image/jpeg"

                    gemini_native_payload = {
                        "contents": [{
                            "parts": [
                                {"text": f"{system_prompt}\n\nПользователь: {user_message if user_message else 'Посмотри на этот скриншот'}"},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": img_data
                                    }
                                }
                            ]
                        }]
                    }
                    
                    # ИСПРАВЛЕНО: Заменили модель на актуальную gemini-2.5-flash
                    response = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key.strip()}",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(gemini_native_payload),
                        timeout=30.0
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Сбой родного Gemini API ({response.status_code}): {response.text}")

                    if response.status_code == 200:
                        res_json = response.json()
                        reply = res_json['candidates'][0]['content']['parts'][0]['text']
                except Exception as e:
                    logger.error(f"Ошибка картинки в родном Gemini: {e}")

            # 2. Попытка через OpenRouter с картинкой (страховка)
            if (reply.startswith("Ошибка") or "Ошибка" in reply) and or_key:
                try:
                    or_image_messages = [{"role": "system", "content": system_prompt}]
                    for msg in history_messages:
                        or_image_messages.append({"role": msg["role"], "content": msg["content"]})
                    or_image_messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_message if user_message else "Посмотри на этот скриншот"},
                            {"type": "image_url", "image_url": {"url": user_image}}
                        ]
                    })
                    
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {or_key.strip()}", "Content-Type": "application/json"},
                        json={"model": "google/gemini-2.5-flash", "messages": or_image_messages},
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        reply = response.json()['choices'][0]['message']['content']
                except Exception as e:
                    logger.error(f"Ошибка картинки в OpenRouter: {e}")

        # ЕСЛИ КАРТИНКИ НЕТ ИЛИ ВСЕ СБОЙНУЛО — СТАНДАРТНЫЙ ТЕКСТОВЫЙ КАСКАД
        if not user_image or (reply.startswith("Ошибка") or "Ошибка" in reply):
            # 1. Попытка Groq
            if groq_key:
                try:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key.strip()}", "Content-Type": "application/json"},
                        json={"model": "llama-3.3-70b-versatile", "messages": text_messages},
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        reply = response.json()['choices'][0]['message']['content']
                except: pass

            # 2. Попытка OpenRouter
            if (reply.startswith("Ошибка") or "Ошибка" in reply) and or_key:
                try:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {or_key.strip()}", "Content-Type": "application/json"},
                        json={"model": "meta-llama/llama-3.3-70b-instruct", "messages": text_messages},
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        reply = response.json()['choices'][0]['message']['content']
                except: pass

            # 3. Попытка Gemini (текстовый)
            if (reply.startswith("Ошибка") or "Ошибка" in reply) and gemini_key:
                try:
                    response = await client.post(
                        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key.strip()}",
                        headers={"Content-Type": "application/json"},
                        json={
                            "contents": [{"parts": [{"text": "\n".join([m["content"] for m in text_messages])}]}]
                        },
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        reply = response.json()['candidates'][0]['content']['parts'][0]['text']
                except: pass
            
    # Сохраняем в БД
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
