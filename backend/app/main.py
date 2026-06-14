from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import databases
import sqlalchemy
import openai
import os
import uuid
from datetime import datetime
from .database import messages, database  # ← импорты из database.py

app = FastAPI()

# 🔥 CORS (разрешаем фронтенд)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chat-ai-frontend-y1bt.
