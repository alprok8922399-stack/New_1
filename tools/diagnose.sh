#!/bin/sh
set -eux
echo "Running diagnose.sh"
ls -la /app || true
cat /app/app/main.py || true
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000"
