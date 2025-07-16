#!/bin/sh
set -e

# host/port of your mongo service (matches docker-compose service name + port)
MONGO_HOST="${MONGO_HOST:-mongo}"
MONGO_PORT="${MONGO_PORT:-27017}"

echo "⏳ Waiting for MongoDB at $MONGO_HOST:$MONGO_PORT…"
echo "⏳ Waiting for MongoDB at $MONGO_URI…"
# loop until nc sees something listening
while ! nc -z "$MONGO_HOST" "$MONGO_PORT"; do
  echo "$(date +'%Y-%m-%dT%H:%M:%S') – still waiting for mongo…" 
  sleep 1
done

echo "✅ MongoDB is up – starting your process"
# exec the CMD from the Dockerfile / docker-compose
# exec "$@"
# exec flask run --host="${FLASK_RUN_HOST:-0.0.0.0}" --port="${FLASK_RUN_PORT:-5000}"

exec python run.py