FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Shared modules are mounted as a volume

# Set environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=api-gateway
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
