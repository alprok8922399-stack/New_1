import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

print("===================================")
print("OPENROUTER_API_KEY EXISTS:", OPENROUTER_API_KEY is not None)

if OPENROUTER_API_KEY:
    print("OPENROUTER_API_KEY LENGTH:", len(OPENROUTER_API_KEY))
else:
    print("OPENROUTER_API_KEY LENGTH: 0")

print("===================================")

MODEL = "deepseek/deepseek-chat-v3-0324"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# =====================
# REQUEST MODEL
# =====================
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# =====================
# CHAT ENDPOINT
# =====================
@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    user_text = req.message

    async with aiohttp.ClientSession() as session:
        async with session.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": user_text
                    }
                ],
            },
        ) as resp:

            data = await resp.json()

            print("===================================")
            print("OPENROUTER STATUS:", resp.status)
            print("OPENROUTER RESPONSE:")
            print(data)
            print("===================================")

    reply = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "Ошибка ответа")
    )

    db = SessionLocal()

    try:
        msg = Message(
            user_message=user_text,
            bot_reply=reply
        )

        db.add(msg)
        db.commit()

    finally:
        db.close()

    return ChatResponse(reply=reply)
