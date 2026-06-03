import os
import asyncio
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn

from . import openai_client  # предполагается, что openai_client имеет async функцию `create_completion`

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    meta: Dict[str, Any] = {}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    prompt = req.message
    try:
        # ожидаем, что openai_client.create_completion — асинхронная функция, которая возвращает строку
        reply = await openai_client.create_completion(prompt)
    except Exception as e:
        # логировать можно здесь при необходимости
        raise HTTPException(status_code=500, detail="OpenAI error: " + str(e))
    return ChatResponse(reply=reply, meta={"model": getattr(openai_client, "MODEL_NAME", "unknown")})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    # uvicorn.run вызывает asyncio loop; при запуске в контейнере Render используйте host 0.0.0.0
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, log_level="info")
  
