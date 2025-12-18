#!/usr/bin/env python3
"""
Entrypoint script for Railway deployment
Handles PORT environment variable properly
"""
import os
import sys
import subprocess

# Get PORT from environment, default to 8080
port = os.environ.get('PORT', '8080')

print(f"Starting PDF Conversion Service on port {port}")
print(f"Python version: {sys.version}")

# Check for LibreOffice
try:
    result = subprocess.run(['which', 'libreoffice'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"LibreOffice found at: {result.stdout.strip()}")
    else:
        print("Warning: LibreOffice not found in PATH")
except Exception as e:
    print(f"Warning: Could not check for LibreOffice: {e}")

# Start gunicorn with proper PORT
cmd = [
    'gunicorn',
    'app:app',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '1',
    '--threads', '4',
    '--timeout', '120',
    '--access-logfile', '-',
    '--error-logfile', '-',
    '--log-level', 'info'
]

print(f"Executing: {' '.join(cmd)}")
os.execvp('gunicorn', cmd)
