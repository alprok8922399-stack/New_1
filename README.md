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
