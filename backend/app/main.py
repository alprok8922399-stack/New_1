from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "ok"}

# 💥 БЕСПЛАТНЫЙ ИИ (без кредитов OpenRouter)
@app.post("/api/chat")
def chat(req: ChatRequest):

    if not req.message:
        return {"response": "Пустое сообщение"}

    try:
        # 🔥 бесплатная модель (HuggingFace)
        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-large",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "inputs": req.message
            },
            timeout=30
        )

        data = response.json()

        # защита от странного ответа
        if isinstance(data, list) and len(data) > 0:
            answer = data[0].get("generated_text", "")
        elif isinstance(data, dict):
            answer = data.get("generated_text", str(data))
        else:
            answer = str(data)

        return {
            "response": "🤖 " + answer
        }

    except Exception as e:
        return {
            "response": "🤖 Ошибка модели (fallback): " + req.message
        }
