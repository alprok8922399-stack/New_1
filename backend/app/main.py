from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# 🔥 ВАЖНО: правильный CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chat-ai-frontend-y1bt.onrender.com",
        "http://localhost",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.message:
        return {"response": "Пустое сообщение"}

    return {
        "response": "🤖 Ответ: " + req.message
    }
