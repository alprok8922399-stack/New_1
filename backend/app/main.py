

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import asyncio
from . import openai_client

app = FastAPI()

@app.post("/api/chat")
async def chat_endpoint(req: Request):
data = await req.json()
message = data.get("message", "")
try:
if asyncio.iscoroutinefunction(getattr(openai_client, "get_reply", None)):
reply = await openai_client.get_reply(message)
elif asyncio.iscoroutinefunction(getattr(openai_client, "async_get_reply", None)):
reply = await openai_client.async_get_reply(message)
else:
loop = asyncio.get_running_loop()
sync_fn = getattr(openai_client, "send_message", None) or getattr(openai_client, "get_reply")
reply = await loop.run_in_executor(None, sync_fn, message)
except Exception as e:
return JSONResponse(status_code=500, content={"error": str(e)})
return {"reply": reply}

if name == "__main__":
port = int(os.environ.get("PORT", "8000"))
import uvicorn
uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, log_level="info")