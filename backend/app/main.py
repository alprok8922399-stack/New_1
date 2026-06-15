import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Настройка CORS, чтобы телефон и фронтенд могли подключаться к бэкенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(request: MessageRequest):
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {"reply": "Ошибка бэкенда: Переменная OPENROUTER_API_KEY не найдена на Render."}

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {"role": "user", "content": request.message}
            ]
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=data, timeout=30.0)
                
                if response.status_code != 200:
                    return {"reply": f"Ошибка OpenRouter (Код {response.status_code}): {response.text}"}
                
                result = response.json()
                reply = result["choices"][0]["message"]["content"]
                return {"reply": reply}
                
            except httpx.RequestError as exc:
                return {"reply": f"Сетевая ошибка при запросе к OpenRouter: {exc}"}
                
    except Exception as e:
        # Перехватываем вообще любую ошибку и выводим её текст прямо в чат бота
        return {"reply": f"Критическая ошибка на сервере: {str(e)}"}
