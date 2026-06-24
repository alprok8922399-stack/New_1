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

async def search_internet(query: str, max_results: int = 3) -> str:
    """Ищет информацию в интернете через DuckDuckGo и возвращает результаты со ссылками."""
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://html.duckduckgo.com/html/?q={httpx.encode_uri(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = await client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code != 200:
                return "Не удалось получить результаты поиска."
                
            html = response.text
            results = []
            
            # Поиск блоков результатов на странице HTML
            matches = re.findall(r'<a class="result__url" href="([^"]+)">.*?<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
            
            if not matches:
                links = re.findall(r'href="([^"]+)" class="result__snippet"', html)
                snippets = re.findall(r'class="result__snippet">([^<]+)', html)
                matches = list(zip(links, snippets))

            for link, snippet in matches[:max_results]:
                clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                if "//duckduckgo.com/l/?kh=-1&uddg=" in link:
                    link = link.split("uddg=")[1].split("&")[0]
                    link = httpx.unquote(link)
                results.append(f"- {clean_snippet}\n  Ссылка: {link}")
                
            if not results:
                return "Поиск не дал результатов."
                
            return "\n\n".join(results)
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return "Произошла ошибка при поиске в интернете."

async def check_if_search_needed(user_message: str) -> bool:
    """Проверяет триггер-слова в сообщении для запуска поиска."""
    keywords = ["найди", "погугли", "интернет", "ссылк", "новости", "что сейчас", "какой сегодня", "актуальн", "узнай"]
    msg_lower = user_message.lower()
    return any(kw in msg_lower for kw in keywords)

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
    user_image = data.get("image") or ""
    requested_model = data.get("model") or "auto"  # Получаем принудительную модель из интерфейса
    
    time_match = re.search(r"Текущие дата и время:\s*([^\]]+)", raw_user_message)
    client_time = time_match.group(1).strip() if time_match else "Неизвестно"
    name_match = re.search(r"Имя собеседника:\s*([^\]]+)", raw_user_message)
    user_name = name_match.group(1).strip() if name_match else "Алексей"

    user_message = re.sub(r"^\[Системное инфо.*?\]\s*", "", raw_user_message, flags=re.DOTALL).strip()
    
    # Запуск интернет-поиска при обнаружении ключевых слов
    search_results = ""
    if await check_if_search_needed(user_message):
        logger.info(f"Запуск поиска в интернете для запроса: {user_message}")
        search_query = re.sub(r"\b(найди|погугли|в интернете|скажи|интернет|пожалуйста)\b", "", user_message, flags=re.IGNORECASE).strip()
        if not search_query:
            search_query = user_message
            
        search_results = await search_internet(search_query)

    groq_key = os.environ.get("GROQ_KEY") or os.environ.get("GROG_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    or_key = os.environ.get("OPENROUTER_API_KEY")
    
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

    system_prompt = f"Ты — friend and helper. Пользователя зовут {user_name}. Текущие дата и время: {client_time}. Отвечай кратко, с юмором, на русском."
    
    # Добавляем результаты поиска в системный промпт, если они есть
    if search_results:
        system_prompt += f"\n\nИНФОРМАЦИЯ ИЗ ИНТЕРНЕТА ДЛЯ ТВОЕГО ОТВЕТА (используй эти данные и обязательно прикрепи ссылки к своему ответу):\n{search_results}"

    text_messages = [{"role": "system", "content": system_prompt}]
    for msg in history_messages:
        text_messages.append({"role": msg["role"], "content": msg["content"]})
    text_messages.append({"role": "user", "content": user_message if user_message else "Посмотри на этот скриншот"})
    
    reply = "Ошибка: выбранный сервис недоступен"
    model_used = "none"
    
    async with httpx.AsyncClient() as client:
        
        # 1. ПОПЫТКА GEMINI (Если авто-режим или выбран вручную)
        if (requested_model in ["auto", "gemini"]) and gemini_key:
            try:
                # Формируем структуру под картинку или под текст
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

        # 2. ПОПЫТКА OPENROUTER (Если авто-режим или выбран вручную, и первая модель не ответила)
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

        # 3. ПОПЫТКА GROQ (Каскад последней надежды или ручной выбор)
        if (reply.startswith("Ошибка") and requested_model == "auto" or requested_model == "groq") and groq_key:
            try:
                # Если была картинка, добавляем текстовую подсказку для Groq в промпт
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
            
    # Сохраняем историю в БД (с краткой меткой контекста скриншота, чтобы не жрать токены!)
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
