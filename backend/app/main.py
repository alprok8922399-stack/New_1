import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import openai_client

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    meta: Dict[str, Any] = {}


@app.get("/")
async def root():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        reply = await openai_client.create_completion(req.message)
        return ChatResponse(
            reply=reply,
            meta={"model": openai_client.MODEL_NAME},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
