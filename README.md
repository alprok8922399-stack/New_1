# Chat AI (FastAPI backend + static frontend)

Кратко:
- backend: backend/Dockerfile -> запускает FastAPI на 8000, маршрут POST /api/chat
- frontend: static site в папке frontend (index.html, main.js)
- CI: GitHub Actions проверяет сборку зависимостей и синтаксис

Deploy на Render (быстрые шаги):
1. Создать Web Service:
   - Environment: Docker
   - Dockerfile path: backend/Dockerfile
   - Branch: main
   - Добавить ENV OPENAI_API_KEY (в Settings → Environment)
2. Создать Static Site:
   - Publish directory: frontend
3. После деплоя заменить в frontend/main.js BACKEND = "/api/chat" на полный URL: "https://<ваш-бекенд>.onrender.com/api/chat", закоммитить и дождаться redeploy.

Тесты:
- Откройте публичный URL статического сайта, отправьте сообщение.
- Если ошибка — смотрите логи бэкенда и Network запрос к /api/chat.
- 
Quick start (local, Docker)
Copy .env.example → .env and set OPENAI_API_KEY if available.
Build image: docker build -t new1-backend -f backend/Dockerfile .
Run container: docker run --env-file .env -p 8000:8000 new1-backend
Open frontend by serving frontend/ (or open frontend/index.html) and point API requests to http://localhost:8000/api/chat

# PROJECT STATUS

## Project

New_1 — веб-чат с ИИ на базе FastAPI, Render и OpenRouter.

## Current Status

Project is operational and publicly accessible.

Frontend:
https://chat-ai-frontend-y1bt.onrender.com

Backend:
https://new-1-5155.onrender.com

API Docs:
https://new-1-5155.onrender.com/docs

## Completed

* GitHub repository configured
* Backend deployed on Render
* FastAPI configured and running
* Docker deployment fixed
* Import/package issues fixed
* Exit 128 deployment issue resolved
* OpenRouter integration completed
* DeepSeek model connected
* Frontend deployed on Render
* CORS configured
* Frontend successfully connected to Backend
* Chat responses working

## AI Model

Current model:

deepseek/deepseek-chat-v3-0324

Provider:

OpenRouter

## Verified

User message:

Привет

AI response:

Привет! 😊 Как я могу помочь тебе сегодня?

## Next Development Steps

1. Improve UI/UX design
2. Add conversation history
3. Add memory/context between messages
4. Add typing indicator
5. Add model selection
6. Add custom domain
7. Add user accounts
8. Add database storage

## Last Verified

2026-06-05

System fully operational.

