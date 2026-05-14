# backend/app/main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .openai_client import OpenAIClient, OpenAIError

class ChatRequest(BaseModel):
    message: str

app = FastAPI(title="Chat AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    # allow startup but raise on calls
    OPENAI_KEY = None

client = OpenAIClient(api_key=OPENAI_KEY)

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")
    try:
        reply = client.simple_completion(req.message)
        return {"reply": reply}
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=str(e))
