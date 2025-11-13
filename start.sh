#!/bin/bash
# Start script for Railway deployment
# Railway automatically sets PORT environment variable

# Default to 8080 if PORT is not set
PORT=${PORT:-8080}

echo "Starting PDF Conversion Service on port $PORT"
echo "LibreOffice check..."
which libreoffice || echo "Warning: LibreOffice not found in PATH"

# Start gunicorn with the PORT from environment
exec gunicorn app:app \
  --bind "0.0.0.0:${PORT}" \
  --workers 2 \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
