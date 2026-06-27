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

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url: return None
    try:
        return psycopg2.connect(db_url, connect_timeout=3)
    except Exception as e:
        logger.error(f"БД ошибка: {e}")
        return None

async def search_tavily(query: str, api_key: str) -> str:
    """Функция для поиска информации в интернете через Tavily API"""
    if not api_key:
        return ""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key.strip(),
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": False,
                    "max_results": 3
                },
                timeout=10.0
            )
            if response.status_code == 200:
                results = response.json().get("results", [])
                if not results:
                    return "\n[Поиск в интернете не дал результатов]\n"
                
                search_context = "\n--- РЕЗУЛЬТАТЫ ПОИСКА В ИНТЕРНЕТЕ ---\n"
                for idx, res in enumerate(results, 1):
                    search_context += f"Источник {idx}: {res.get('title')}\nURL: {res.get('url')}\nСодержание: {res.get('content')}\n\n"
                search_context += "-------------------------------------\n"
                return search_context
            else:
                logger.error(f"Ошибка Tavily API: {response.text}")
                return ""
    except Exception as e:
        logger.error(f"Сбой при поиске Tavily: {e}")
        return ""

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
    
    groq_key = os.environ.get("GROQ_KEY") or os.environ.get("GROG_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    or_key = os.environ.get("OPENROUTER_API_KEY")
    tavily_key = os.environ.get("TAVILY_API_KEY")
    
    # АВТОМАТИЧЕСКИЙ ПОИСК В ИНТЕРНЕТЕ (TAVILY)
    search_data = ""
    keywords = ["найди", "поиск", "интернет", "гугл", "ссылк", "узнай", "информац"]
    if any(word in user_message.lower() for word in keywords) and tavily_key:
        logger.info(f"Запуск веб-поиска для запроса: {user_message}")
        search_data = await search_tavily(user_message, tavily_key)

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

    # ОБНОВЛЕННЫЙ ПРОМПТ ДЛЯ КРАСИВОГО СТРУКТУРИРОВАННОГО ОТВЕТА С ЭМОДЗИ И ОТСТУПАМИ
    system_prompt = (
        f"Ты — друг и помощник. Пользователя зовут {user_name}. Текущие дата и время: {client_time}. "
        f"Отвечай развернуто, структурировано, с легким юмором, строго на русском языке. "
        f"ОФОРМЛЕНИЕ И СТИЛЬ: Твой ответ ОБЯЗАТЕЛЬНО должен быть визуально привлекательным. "
        f"Разделяй мысли на логические абзацы. Используй списки (маркированные или нумерованные) для перечислений. "
        f"Обязательно используй жирный шрифт для выделения важных заголовков и ключевых моментов. "
        f"Щедро используй тематические эмодзи (например: 🚀, ⚙️, ✨, 🛠️, 📊, 📝) в начале заголовков и пунктов списков, чтобы оживить текст. "
        f"ВАЖНО: Если к запросу прикреплены 'РЕЗУЛЬТАТЫ ПОИСКА В ИНТЕРНЕТЕ', обязательно используй их для ответа. "
        f"Все ссылки на источники делай СТРОГО кликабельными, упаковывая их в формат Markdown, например: [Название сайта](URL-ссылка). "
        f"Пользователь должен иметь возможность нажать на название источника и перейти по ссылке."
    )
    
    text_messages = [{"role": "system", "content": system_prompt}]
    for msg in history_messages:
        text_messages.append({"role": msg["role"], "content": msg["content"]})
        
    final_user_content = user_message
    if search_data:
        final_user_content = f"{user_message}\n{search_data}"
        
    text_messages.append({"role": "user", "content": final_user_content if final_user_content else "Посмотри на этот скриншот"})
    
    reply = "Ошибка: выбранный сервис недоступен"
    model_used = "none"
    
    async with httpx.AsyncClient() as client:
        
        # 1. ПОПЫТКА GROQ
        if (requested_model in ["auto", "groq"]) and groq_key:
            try:
                groq_messages = text_messages.copy()
                if user_image:
                    groq_messages[-1]["content"] = f"[Пользователь отправил скриншот. Проанализируй контекст обсуждения] {final_user_content}".strip()

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

        # 2. ПОПЫТКА GEMINI
        if (reply.startswith("Ошибка") and requested_model == "auto" or requested_model == "gemini") and gemini_key:
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
                                {"text": f"{system_prompt}\n\nПользователь: {final_user_content if final_user_content else 'Посмотри на скриншот'}"},
                                {"inline_data": {"mime_type": mime_type, "data": img_data}}
                            ]
                        }]
                    }
                else:
                    gemini_payload = {
                        "contents": [{
                            "parts": [{"text": f"{system_prompt}\n\nПользователь: {final_user_content}"}]
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


        # 3. ПОПЫТКА OPENROUTER
        if (reply.startswith("Ошибка") and requested_model == "auto" or requested_model == "openrouter") and or_key:
            try:
                if user_image:
                    or_messages = [{"role": "system", "content": system_prompt}]
                    for msg in history_messages:
                        or_messages.append({"role": msg["role"], "content": msg["content"]})
                    or_messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": final_user_content if final_user_content else "Посмотри на скриншот"},
                            {"type": "image_url", "image_url": {"url": user_image}}
                        ]
                    })
                else:
                    or_messages = text_messages

                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {or_key.strip()}", "Content-Type": "application/json"},
                    json={"model": "openrouter/auto", "messages": or_messages},
                    timeout=30.0
                )
                if response.status_code == 200:
                    reply = response.json()['choices'][0]['message']['content']
                    model_used = "openrouter"
            except Exception as e:
                logger.error(f"Сбой OpenRouter: {e}")
            
    # Сохраняем историю в БД
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
