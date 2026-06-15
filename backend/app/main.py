import os
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем доступ для твоего фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        # Получаем данные из чата
        data = await request.json()
        
        # Берем текст сообщения
        user_message = data.get("text") or data.get("message") or ""
        
        if not user_message:
            return {"text": "Ошибка: Бэкенд получил пустое сообщение."}

        # Получаем ключ OpenRouter из настроек Render
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        
        if not api_key:
            return {"text": "Ошибка: OPENROUTER_API_KEY не найден в настройках Environment на Render."}
        
        # Делаем прямой запрос к нейросети
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/llama-3-8b-instruct:free",  # Стабильная бесплатная модель Llama 3
                    "messages": [
                        {"role": "system", "content": "Ты вежливый ИИ-помощник в чате. Отвечай кратко и по делу."},
                        {"role": "user", "content": user_message}
                    ]
                },
                timeout=30.0
            )
            
            # Если нейросеть ответила успешно
            if response.status_code == 200:
                result = response.json()
                reply = result['choices'][0]['message']['content']
            else:
                reply = f"Ошибка ИИ (Код {response.status_code}): Ошибка со стороны OpenRouter. Проверь баланс ключа или сам ключ."

        return {"text": reply}
        
    except Exception as e:
        return {"text": f"Ошибка бэкенда: {str(e)}"}
