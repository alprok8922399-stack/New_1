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
