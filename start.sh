#!/bin/sh
set -e
PORT="${PORT:-8080}"
echo "Starting CRM on 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
