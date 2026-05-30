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
ENV PORT=8000
CMD ["/tools/diagnose.sh"]
