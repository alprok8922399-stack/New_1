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
    # Теперь используем корректное имя переменной
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="Ошибка: OPENROUTER_API_KEY отсутствует в настройках Render"
        )

    # Используем базовый URL OpenRouter и стабильную бесплатную модель для теста
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
            
            # Если OpenRouter вернул ошибку, мы перехватим её здесь
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Ошибка OpenRouter: {response.text}"
                )
            
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            return {"reply": reply}
            
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=500, 
                detail=f"Сетевая ошибка при запросе к ИИ: {exc}"
            )
