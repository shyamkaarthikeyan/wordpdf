# Use Python 3.9 slim image
FROM python:3.9-slim

# Install LibreOffice and required dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.py

# Expose port (Railway will override with its own PORT)
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application using Python entrypoint (no shell issues)
CMD ["python3", "entrypoint.py"]
