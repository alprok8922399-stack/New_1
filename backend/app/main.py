from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict

from app.openai_client import create_completion

app = FastAPI()

# 🧠 память на сервере (в RAM)
chat_sessions: Dict[str, List[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = "user-1"


class ChatResponse(BaseModel):
    reply: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):

    # создаём сессию если её нет
    if req.session_id not in chat_sessions:
        chat_sessions[req.session_id] = []

    history = chat_sessions[req.session_id]

    # добавляем сообщение пользователя
    history.append({
        "role": "user",
        "content": req.message
    })

    # отправляем всю историю в ИИ
    reply = await create_completion(history)

    # добавляем ответ ИИ
    history.append({
        "role": "assistant",
        "content": reply
    })

    return ChatResponse(reply=reply)
