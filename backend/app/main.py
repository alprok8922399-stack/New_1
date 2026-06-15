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
        image_base64 = data.get("image") or "" # Получаем фото от телефона, если оно есть
        
        if not user_message and not image_base64:
            return {"text": "Ошибка: Бэкенд получил пустое сообщение."}

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            return {"text": "Ошибка: OPENROUTER_API_KEY отсутствует в настройках Render."}
        
        # Собираем содержимое сообщения для нейросети
        content_list = []
        if user_message:
            content_list.append({"type": "text", "text": user_message})
        
        if image_base64:
            # Форматируем картинку так, как требует OpenRouter
            content_list.append({
                "type": "image_url",
                "image_url": {
                    "url": image_base64 # Передаем строку картинки
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
                    "model": "meta-llama/llama-3-8b-instruct",
                    "messages": [
                        {"role": "user", "content": content_list} # Отправляем текст + фото вместе
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
