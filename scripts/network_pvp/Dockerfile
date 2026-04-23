FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose WebSocket port
EXPOSE 8765

# Run server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8765"]
