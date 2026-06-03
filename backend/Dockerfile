FROM python:3.11-slim AS builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend /app
COPY tools /tools
ENV PYTHONUNBUFFERED=1
CMD ["sh", "-lc", "echo STARTING; echo PORT=$PORT; env; ls -la /app; ls -la /usr/local/bin; which python || true; python --version || true; python -m pip show uvicorn || true; exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
