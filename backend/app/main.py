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
        
        if not user_message:
            return {"text": "Ошибка: Бэкенд получил пустое сообщение."}

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        # ОТЛАДКА: выведет длину ключа в логи Render (сам ключ не покажет)
        print(f"DEBUG: Key loaded, length: {len(api_key)}")
        
        if not api_key:
            return {"text": "Ошибка: OPENROUTER_API_KEY не найден в настройках."}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemma-2-27b-it:free",
                    "messages": [
                        {"role": "system", "content": "Ты вежливый ИИ-помощник."},
                        {"role": "user", "content": user_message}
                    ]
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result['choices'][0]['message']['content']
            else:
                reply = f"Ошибка ИИ (Код {response.status_code}): Проверь ключ."

        return {"text": reply}
        
    except Exception as e:
        return {"text": f"Ошибка бэкенда: {str(e)}"}
