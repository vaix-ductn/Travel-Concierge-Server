#!/bin/bash

# Function to cleanup child processes
cleanup() {
    echo "Received SIGTERM/SIGINT, cleaning up..."
    kill $(jobs -p)
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