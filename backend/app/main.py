from fastapi import FastAPI, Request
app = FastAPI()
@app.post("/api/chat")
async def chat(request: Request):
data = await request.json()
prompt = data.get("message", "")
return {"reply": f"Echo: {prompt}"}
