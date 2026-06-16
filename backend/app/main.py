import os
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


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
