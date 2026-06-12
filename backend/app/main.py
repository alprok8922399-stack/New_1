from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# 🔥 CORS (разрешаем фронтенд)
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

# ====== МОДЕЛЬ ======
class ChatRequest(BaseModel):
    message: str

# ====== ROOT ======
@app.get("/")
def root():
    return {"status": "ok"}

# ====== CHAT ======
@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.message:
        return {"response": "Пустое сообщение"}

    msg = req.message.lower()

    # простая логика (без БД и без пользователей)
    if "привет" in msg:
        answer = "Привет! 👋"
    elif "как меня зовут" in msg:
        answer = "Я пока не знаю твоего имени 🙂"
    elif "что ты умеешь" in msg:
        answer = "Я простой рабочий чат. Без базы и без пользователей, но стабильно 🙂"
    elif "пока" in msg:
        answer = "Пока! 👋"
    else:
        answer = "Я получил: " + req.message

    return {
        "response": "🤖 " + answer
    }
