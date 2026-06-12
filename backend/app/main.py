from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS (чтобы фронт работал)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== МОДЕЛЬ ЗАПРОСА ======
class ChatRequest(BaseModel):
    message: str

# ====== ИИ ОТВЕТ (ЗАГЛУШКА) ======
def generate_answer(text: str) -> str:
    # тут потом подключишь GPT / свою модель
    return f"🤖 Ответ: {text}"

# ====== ОСНОВНОЙ ЧАТ ======
@app.post("/chat")
def chat(req: ChatRequest):
    if not req.message:
        return {"response": "Пустое сообщение"}

    answer = generate_answer(req.message)

    return {
        "response": answer
    }

# ====== ПРОВЕРКА СЕРВЕРА ======
@app.get("/")
def root():
    return {"status": "ok"}
