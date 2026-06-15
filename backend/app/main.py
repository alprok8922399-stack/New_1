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

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        user_message = data.get("text") or ""
        image_base64 = data.get("image") or ""
        
        # Инструкция для ИИ
        system_prompt = "Ты — полезный, вежливый и умный ИИ-помощник. Отвечай всегда на чистом, грамотном русском языке. Пиши развернуто и понятно."

        # Формируем контент
        content = [{"type": "text", "text": user_message}]
        if image_base64:
            content.append({"type": "image_url", "image_url": {"url": image_base64}})

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "qwen/qwen-2.5-7b-instruct", # Стабильная модель
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ]
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                return {"text": reply}
            else:
                return {"text": f"Ошибка {response.status_code}: {response.text}"}
    except Exception as e:
        return {"text": f"Ошибка: {str(e)}"}
