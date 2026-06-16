import os
import httpx
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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

# Лимит символов для одного сообщения (защита от огромных текстов)
MAX_USER_MESSAGE_LENGTH = 8000

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        user_message = data.get("text") or ""
        image_base64 = data.get("image") or ""

        # Логируем начало обработки запроса
        logger.info(f"[{datetime.now()}] Получен запрос. Текст: '{user_message[:50]}...'")

        # Проверка на пустое сообщение (без текста и без картинки)
        if not user_message and not image_base64:
            return {"text": "Пожалуйста, введите сообщение или загрузите изображение."}

        # Обрезаем слишком длинное сообщение пользователя, чтобы не тратить лишние кредиты
        if len(user_message) > MAX_USER_MESSAGE_LENGTH:
            user_message = user_message[:MAX_USER_MESSAGE_LENGTH] + "\n\n[Сообщение было слишком длинным и обрезано для экономии токенов]"

        system_prompt = "Ты — мудрый, вежливый и опытный ИИ-помощник. Отвечай всегда подробно, развернуто и исключительно на русском языке."

        content = [{"type": "text", "text": user_message}]
        if image_base64:
            content.append({"type": "image_url", "image_url": {"url": image_base64}})

        api_key = os.environ.get("OPENROUTER_API_KEY", "")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://chat-ai-frontend-y1bt.onrender.com",
                    "X-Title": "My AI Chat"
                },
                json={
                    "model": "deepseek/deepseek-chat",
                    "max_tokens": 4096,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ]
                },
                timeout=30.0
            )

            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                # Логируем ответ
                logger.info(f"[{datetime.now()}] Ответ получен. Первые символы: '{reply[:10]}...'")
                return {"text": reply}
            else:
                error_msg = f"Ошибка OpenRouter: {response.text}"
                logger.error(f"[{datetime.now()}] {error_msg}")
                return {"text": error_msg}
    except Exception as e:
        error_msg = f"Ошибка бэкенда: {str(e)}"
        logger.error(f"[{datetime.now()}] {error_msg}")
        return {"text": error_msg}
        
