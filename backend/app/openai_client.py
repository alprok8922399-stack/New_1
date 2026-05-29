import os, requests OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") def send_message(message: str, timeout=15): return {"reply": f"Stub reply to: {message}"}
