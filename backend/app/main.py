# импорт по относительному пути — если в CI/Deploy возникают ошибки, менять на absolute (backend.app.openai_client)
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from . import openai_client

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
        # ожидается async функция create_completion(prompt) в openai_client
        reply = await openai_client.create_completion(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")
    return ChatResponse(reply=reply, meta={"model": getattr(openai_client, "MODEL_NAME", "unknown")})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
EOF
