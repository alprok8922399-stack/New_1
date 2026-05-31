from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from . import openai_client

app = FastAPI()

@app.post('/api/chat')
async def chat_endpoint(req: Request):
    data = await req.json()
    prompt = data.get('prompt', '')
    try:
        reply = openai_client.get_reply(prompt)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
    return {'reply': reply}
