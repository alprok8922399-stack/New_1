#!/bin/sh
set -eux
echo "Running diagnose.sh"
echo "PORT=${PORT:-not-set}"
ls -la /app || true
ls -la /tools || true
cat /app/main.py 2>/dev/null || cat /app/app/main.py 2>/dev/null || true
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
