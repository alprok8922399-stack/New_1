from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/api/chat")
def chat(req: ChatRequest):

    if not OPENROUTER_API_KEY:
        return {"response": "❌ API KEY НЕ ЗАГРУЖЕН"}

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-chat",

                # 🔥 КРИТИЧЕСКИЙ ФИКС
                "max_tokens": 300,

                "messages": [
                    {"role": "system", "content": "Ты полезный ассистент."},
                    {"role": "user", "content": req.message}
                ]
            },
            timeout=30
        )

        data = response.json()

        if "choices" not in data:
            return {"response": f"❌ OpenRouter error: {data}"}

        answer = data["choices"][0]["message"]["content"]

        return {
            "response": "🤖 " + answer
        }

    except Exception as e:
        return {
            "response": f"❌ EXCEPTION: {str(e)}"
        }
