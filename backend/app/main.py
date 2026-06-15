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
        
        # Жесткая системная инструкция против иероглифов
        system_prompt = "Ты мудрый ИИ-помощник. Отвечай ВСЕГДА только на русском языке. Использование иностранных языков или иероглифов строго запрещено."

        content = [{"type": "text", "text": user_message}]
        if image_base64:
            content.append({"type": "image_url", "image_url": {"url": image_base64}})

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "meta-llama/llama-3-8b-instruct:free", # Вернули стабильную Llama 3 Free
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
                return {"text": f"Ошибка OpenRouter: {response.text}"}
    except Exception as e:
        return {"text": f"Ошибка: {str(e)}"}
