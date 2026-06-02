from fastapi import FastAPI
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")
logger.info("Starting backend... PORT=%s", os.getenv("PORT"))

app = FastAPI()

@app.get("/_health")
async def health():
logger.info("Health check received")
return {"status":"ok","port":os.getenv("PORT")}
