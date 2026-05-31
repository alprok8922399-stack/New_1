from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from . import openai_client
import asyncio

app = FastAPI()

@app.post('/api/chat')
async def chat_endpoint(req: Request):
    data = await req.json()
    prompt = data.get('prompt', '')
    try:
        # call get_reply in a thread if it's blocking; openai_client should be async ideally
        if asyncio.iscoroutinefunction(openai_client.get_reply):
            reply = await openai_client.get_reply(prompt)
        else:
            loop = asyncio.get_running_loop()
            reply = await loop.run_in_executor(None, openai_client.get_reply, prompt)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
    return {'reply': reply}

# Optional: allow running with `python -m backend.app.main` inside container for local debug
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, log_level="info")
