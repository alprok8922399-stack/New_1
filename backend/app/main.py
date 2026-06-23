import os
import httpx
import logging
import re
import json
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

ADMIN_KEY = os.environ.get("ADMIN_SECRET_KEY")

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url: return None
    try:
        return psycopg2.connect(db_url, connect_timeout=3)
    except Exception as e:
        logger.error(f"БД ошибка: {e}")
        return None

@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_memory (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT NOT NULL
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Таблица chat_memory проверена.")
        except Exception as e:
            logger.error(f"Ошибка инициализации таблицы памяти: {e}")

def save_memory_fact(key, value):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM chat_memory WHERE key = %s", (key,))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE chat_memory SET value = %s WHERE id = %s", (value, row[0]))
            else:
                cur.execute("INSERT INTO chat_memory (key, value) VALUES (%s, %s)", (key, value))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка записи в память: {e}")
    return False

def get_all_memory_context():
    conn = get_db_connection()
    if not conn: return ""
    try:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM chat_memory")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if not rows: return ""
        context = "\n".join([f"- {r[0]}: {r[1]}" for r in rows])
        return f"\n\nВАЖНАЯ ИНФОРМАЦИЯ О СОБЕСЕДНИКЕ:\n{context}"
    except Exception as e:
        logger.error(f"Ошибка чтения памяти: {e}")
        return ""

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    raw_user_message = data.get("text") or ""
    mode = data.get("mode") or "private"
    user_image = data.get("image") or ""
    requested_model = data.get("model") or "auto"
    
    time_match = re.search(r"Текущие дата и время:\s*([^\]]+)", raw_user_message)
    client_time = time_match.group(1).strip() if time_match else "Неизвестно"
    name_match = re.search(r"Имя собеседника:\s*([^\]]+)", raw_user_message)
    user_name = name_match.group(1).strip() if name_match else "Алексей"

    user_message = re.sub(r"^\[Системное инфо.*?\]\s*", "", raw_user_message, flags=re.DOTALL).strip()
    
    groq_key = os.environ.get("GROQ_KEY") or os.environ.get("GROG_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    or_key = os.environ.get("OPENROUTER_API_KEY")
    
    # ----------------------------------------------------
    # АВТОПЕРЕХВАТ ГЕНЕРАЦИИ КАРТИНОК (Пункт 2)
    # ----------------------------------------------------
    image_triggers = [r"\bнарисуй\b", r"\bсгенерируй\b", r"\bсоздай картинку\b", r"\bизобрази\b", r"\bнарисуй мне\b"]
    is_image_request = any(re.search(trigger, user_message, re.IGNORECASE) for trigger in image_triggers)

    if is_image_request and or_key:
        try:
            async with httpx.AsyncClient() as client:
                # Отправляем запрос на генерацию в OpenRouter (используем бесплатный/дешевый SDXL)
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {or_key.strip()}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "stabilityai/stable-diffusion-xl", 
                        "messages": [{"role": "user", "content": user_message}]
                    },
                    timeout=45.0
                )
                if response.status_code == 200:
                    res_json = response.json()
                    # OpenRouter для картинок возвращает текст со ссылкой или сразу URL
                    reply_text = res_json['choices'][0]['message']['content']
                    
                    # Если ссылка пришла текстом, вытаскиваем её или оформляем в тег img
                    urls = re.findall(r'(https?://[^\s]+)', reply_text)
                    if urls:
                        img_url = urls[0].replace(')', '').replace(']', '') # Чистим хвосты макросов
                        reply = f"Вот твой рисунок по запросу «{user_message}»:\n\n<img src='{img_url}' style='max-width: 100%; border-radius: 12px; margin-top: 8px;' />"
                    else:
                        reply = reply_text
                        
                    return {"text": reply, "model_used": "openrouter"}
        except Exception as e:
            logger.error(f"Ошибка генерации картинок: {e}")
            # Если генерация упала, каскад пойдет дальше в обычный текст

    # Если это не генерация картинок, идет стандартный текстовый каскад:
    memory_context = ""
    if mode == "private":
        memory_context = get_all_memory_context()

    system_prompt = f"Ты — friend and helper. Пользователя зовут {user_name}. Текущие дата и время: {client_time}. Отвечай кратко, с юмором, на русском.{memory_context}"
    
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

    text_messages = [{"role": "system", "content": system_prompt}]
    for msg in history_messages:
        text_messages.append({"role": msg["role"], "content": msg["content"]})
    text_messages.append({"role": "user", "content": user_message if user_message else "Посмотри на этот скриншот"})
    
    reply = "Ошибка: выбранный сервис недоступен"
    model_used = "none"
    
    async with httpx.AsyncClient() as client:
        # 1. ПОПЫТКА GEMINI
        if (requested_model in ["auto", "gemini"]) and gemini_key:
            try:
                if user_image:
                    if "," in user_image:
                        img_data = user_image.split(",")[1]
                        mime_type = user_image.split(";")[0].replace("data:", "")
                    else:
                        img_data = user_image
                        mime_type = "image/jpeg"
                    
                    gemini_payload = {
                        "contents": [{
                            "parts": [
                                {"text": f"{system_prompt}\n\nПользователь: {user_message if user_message else 'Посмотри на скриншот'}"},
                                {"inline_data": {"mime_type": mime_type, "data": img_data}}
                            ]
                        }]
                    }
                else:
                    gemini_payload = {
                        "contents": [{
                            "parts": [{"text": f"{system_prompt}\n\nПользователь: {user_message}"}]
                        }]
                    }

                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key.strip()}",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(gemini_payload),
                    timeout=30.0
                )
                if response.status_code == 200:
                    reply = response.json()['candidates'][0]['content']['parts'][0]['text']
                    model_used = "gemini"
            except Exception as e:
                logger.error(f"Сбой Gemini: {e}")

        # 2. ПОПЫТКА OPENROUTER (Текст)
        if (reply.startswith("Ошибка") and requested_model == "auto" or requested_model == "openrouter") and or_key:
            try:
                if user_image:
                    or_messages = [{"role": "system", "content": system_prompt}]
                    for msg in history_messages:
                        or_messages.append({"role": msg["role"], "content": msg["content"]})
                    or_messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_message if user_message else "Посмотри на скриншот"},
                            {"type": "image_url", "image_url": {"url": user_image}}
                        ]
                    })
                else:
                    or_messages = text_messages

                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {or_key.strip()}", "Content-Type": "application/json"},
                    json={"model": "google/gemini-2.5-flash", "messages": or_messages},
                    timeout=30.0
                )
                if response.status_code == 200:
                    reply = response.json()['choices'][0]['message']['content']
                    model_used = "openrouter"
            except Exception as e:
                logger.error(f"Сбой OpenRouter: {e}")

        # 3. ПОПЫТКА GROQ
        if (reply.startswith("Ошибка") and requested_model == "auto" or requested_model == "groq") and groq_key:
            try:
                groq_messages = text_messages.copy()
                if user_image:
                    groq_messages[-1]["content"] = f"[Пользователь отправил скриншот. Проанализируй контекст обсуждения] {user_message}".strip()

                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key.strip()}", "Content-Type": "application/json"},
                    json={"model": "llama-3.3-70b-versatile", "messages": groq_messages},
                    timeout=30.0
                )
                if response.status_code == 200:
                    reply = response.json()['choices'][0]['message']['content']
                    model_used = "groq"
            except Exception as e:
                logger.error(f"Сбой Groq: {e}")
            
    if mode == "private" and not reply.startswith("Ошибка"):
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            db_user_text = user_message if user_message else "Отправлен скриншот"
            if user_image and user_message:
                db_user_text = f"[Скриншот] {user_message}"
            
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("user", db_user_text))
            cur.execute("INSERT INTO chat_messages (role, content) VALUES (%s, %s)", ("assistant", reply))
            conn.commit()
            cur.close()
            conn.close()

            memory_triggers = {
                "Любимый стиль тату": r"(?:люблю|нравятся?|тащусь от) тату (?:в стиле|стиля?)?\s*([\w\s-]+)",
                "Город проживания": r"(?:живу в|город|из города)\s*([\w\s-]+)",
                "День рождения": r"мой день рождения\s*([\d\.\w]+)"
            }

            for fact_key, pattern in memory_triggers.items():
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    extracted_fact = match.group(1).strip()
                    save_memory_fact(fact_key, extracted_fact)
            
    return {"text": reply, "model_used": model_used}

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
