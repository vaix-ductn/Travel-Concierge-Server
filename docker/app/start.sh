#!/bin/bash

# Function to cleanup child processes
cleanup() {
    echo "Received SIGTERM/SIGINT, cleaning up..."
    echo "Stopping ADK web server (PID: $ADK_PID)..."
    kill $ADK_PID 2>/dev/null
    echo "Stopping Voice Chat WebSocket server (PID: $VOICE_PID)..."
    kill $VOICE_PID 2>/dev/null
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Create log directory if it doesn't exist
mkdir -p /var/www/logs

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z travel_concierge_db 3306; do
  sleep 1
done
echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
cd /var/www
python manage.py migrate

# Start ADK web server in the background
echo "Starting ADK web server..."
adk web --host 0.0.0.0 --port 8002 &
ADK_PID=$!

# Check if ADK server started successfully
if ! ps -p $ADK_PID > /dev/null; then
    echo "Failed to start ADK web server"
    exit 1
fi

# Start Voice Chat WebSocket server in the background
echo "Starting Voice Chat WebSocket server..."
python manage.py start_voice_server --host 0.0.0.0 --port 8003 > /var/www/logs/voice_server.log 2>&1 &
VOICE_PID=$!

# Wait a moment for voice server to initialize
sleep 2

# Check if Voice server started successfully
if ! ps -p $VOICE_PID > /dev/null; then
    echo "Failed to start Voice Chat WebSocket server"
    echo "Check logs: /var/www/logs/voice_server.log"
    exit 1
fi

echo "Voice Chat WebSocket server started successfully (PID: $VOICE_PID)"

# Start Django application
echo "Starting Django application..."
python -X frozen_modules=off -m debugpy --listen 0.0.0.0:5678 -m gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --timeout 3600 \
    --reload \
    --access-logfile /var/www/logs/access.log \
    --error-logfile /var/www/logs/error.log \
    --capture-output \
    --log-level debug

# Exit with status of process that exited
exit $?