#!/bin/bash

# Production startup script for Travel Server
# Runs both Django application and ADK Agent server

# Function to cleanup child processes
cleanup() {
    echo "Received SIGTERM/SIGINT, cleaning up..."
    echo "Stopping ADK Agent server (PID: $ADK_PID)..."
    kill $ADK_PID 2>/dev/null
    echo "Stopping Django server (PID: $DJANGO_PID)..."
    kill $DJANGO_PID 2>/dev/null
    if [ ! -z "$CLOUD_SQL_PID" ]; then
        echo "Stopping Cloud SQL Proxy (PID: $CLOUD_SQL_PID)..."
        kill $CLOUD_SQL_PID 2>/dev/null
    fi
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Create log directory if it doesn't exist
mkdir -p logs

# Start Cloud SQL Proxy if using Cloud SQL
if [ "$ENVIRONMENT" = "production" ] && [ "$DB_HOST" = "127.0.0.1" ]; then
    echo "Starting Cloud SQL Proxy..."
    /usr/local/bin/cloud_sql_proxy -instances=travelapp-461806:us-central1:travel-concierge-db=tcp:3306 &
    CLOUD_SQL_PID=$!

    # Wait for Cloud SQL Proxy to be ready
    echo "Waiting for Cloud SQL Proxy..."
    sleep 5

    # Wait for database to be ready
    echo "Waiting for database..."
    while ! nc -z 127.0.0.1 3306; do
        sleep 1
    done
    echo "Database is ready!"
elif [ ! -z "$DB_HOST" ]; then
    echo "Waiting for database..."
    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 1
    done
    echo "Database is ready!"
fi

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Start ADK Agent server in the background
echo "Starting ADK Agent server..."
adk api_server travel_concierge --host 0.0.0.0 --port 8002 &
ADK_PID=$!

# Check if ADK server started successfully
sleep 3
if ! ps -p $ADK_PID > /dev/null; then
    echo "Failed to start ADK Agent server"
    echo "ADK Agent server logs:"
    # Try to get any error output
    exit 1
fi

echo "ADK Agent server started successfully (PID: $ADK_PID) on port 8002"

# Start Django application
echo "Starting Django application..."
gunicorn --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --worker-class gthread \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    config.wsgi:application &
DJANGO_PID=$!

# Check if Django started successfully
sleep 3
if ! ps -p $DJANGO_PID > /dev/null; then
    echo "Failed to start Django application"
    exit 1
fi

echo "Django application started successfully (PID: $DJANGO_PID) on port 8000"

# Wait for both processes
wait