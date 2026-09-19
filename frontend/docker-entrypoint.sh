#!/bin/sh
set -e
export PORT="${PORT:-80}"
export BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-http://backend.railway.internal:8000}"
envsubst '${PORT} ${BACKEND_UPSTREAM}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
