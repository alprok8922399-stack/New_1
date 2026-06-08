import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sqlalchemy import create_engine, Column, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

import aiohttp

# =====================
# APP
# =====================

app = FastAPI()

# =====================
# CORS
# =====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# FRONTEND PATH
# =====================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def home():
    index_path = os.path.join(FRONTEND_DIR, "index.html")

    if os.path.exists(index_path):
        return FileResponse(index_path)

    return {"status": "ok", "message": "frontend not found"}

# =====================
# DB
# =====================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text)
    bot_reply = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# =====================
# OPENROUTER
# =====================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "deepseek/deepseek-chat-v3-0324"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str


SYSTEM_PROMPT = """
Отвечай в чистом Markdown.

Правила:
- Используй заголовки (#, ##) когда это уместно.
- Используй списки.
- Используй **жирный текст**.
- Для кода используй тройные обратные кавычки.
- Не экранируй Markdown.
- Отвечай на русском языке.
"""


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    user_text = req.message

    db = SessionLocal()

    try:
        history_rows = (
            db.query(Message)
            .order_by(Message.id.desc())
            .limit(10)
            .all()
        )

        history_rows.reverse()

        messages_payload = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        for row in history_rows:
            messages_payload.append(
                {"role": "user", "content": row.user_message}
            )
            messages_payload.append(
                {"role": "assistant", "content": row.bot_reply}
            )

        messages_payload.append(
            {"role": "user", "content": user_text}
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": messages_payload,
                },
            ) as resp:

                # 🔥 ВАЖНАЯ ЗАЩИТА
                if resp.status != 200:
                    error_text = await resp.text()
                    return {"reply": "Ошибка OpenRouter: " + error_text}

                try:
                    data = await resp.json()
                except Exception:
                    text = await resp.text()
                    ка JSON от OpenRouter: " + text}

        reply = str(data)
        

        msg = Message(
            user_message=user_text,
            bot_reply=reply
        )

        db.add(msg)
        db.commit()

        return ChatResponse(reply=reply)

    finally:
        db.close()
