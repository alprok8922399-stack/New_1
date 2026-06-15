import os
import json
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

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        user_message = data.get("text") or data.get("message") or ""
        image_base64 = data.get("image") or ""
        
        if not user_message and not image_base64:
            return {"text": "Ошибка: Бэкенд получил пустое сообщение."}

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            return {"text": "Ошибка: OPENROUTER_API_KEY отсутствует."}
        
        content_list = []
        if user_message:
            content_list.append({"type": "text", "text": user_message})
        
        if image_base64:
            content_list.append({
                "type": "image_url",
                "image_url": {
                    "url": image_base64
                }
            })

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    # Включаем Qwen 2 — она бесплатная, мощная и отлично знает русский язык
                    "model": "qwen/qwen-2-7b-instruct:free",
                    "max_tokens": 1000,
                    "messages": [
                        {"role": "system", "content": "Ты мудрый, вежливый ИИ-помощник. Отвечай всегда подробно, развернуто, грамотно и исключительно на русском языке."},
                        {"role": "user", "content": content_list}
                    ]
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result['choices'][0]['message']['content']
                return {"text": reply}
            else:
                try:
                    error_details = response.json()
                except:
                    error_details = response.text
                return {"text": f"OpenRouter ошибка (Код {response.status_code}): {error_details}"}
        
    except Exception as e:
        return {"text": f"Ошибка бэкенда: {str(e)}"}
