#!/bin/sh
set -eux
echo "Running diagnose.sh"
env || true
echo "PORT=${PORT:-not-set}"
echo "PWD=$(pwd)"
ls -la / || true
ls -la /app || true
ls -la /tools || true
if [ -f /tools/diagnose.sh ]; then file /tools/diagnose.sh || true; fi
cat /app/app/main.py 2>/dev/null || cat /app/main.py 2>/dev/null || true
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
