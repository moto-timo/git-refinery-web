#!/bin/bash

echo "Preparing static files"
cd /usr/src/app
./manage.py collectstatic --no-input

echo Starting nginx.
nginx || exit 1

NUM_WORKERS=3
TIMEOUT=500

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn gitrefinery.wsgi:application \
    --workers $NUM_WORKERS \
    --timeout $TIMEOUT \
    --bind 127.0.0.1:8080
