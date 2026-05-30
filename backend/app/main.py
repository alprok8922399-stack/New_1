from fastapi import FastAPI, Request
import os

app = FastAPI()

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    prompt = data.get("message", "")
    return {"reply": f"Echo: {prompt}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
  
