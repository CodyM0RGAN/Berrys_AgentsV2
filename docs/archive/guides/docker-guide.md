# Docker Best Practices Guide

This guide outlines best practices for working with Docker in the Berrys_AgentsV2 project, focusing on multi-package projects where multiple services share common code.

## Quick Reference

- Use volume mounting for shared code during development
- Be consistent in how shared dependencies are handled across services
- Document the approach in comments and Dockerfiles
- Test Docker builds early and frequently
- Consider environment differences between development and production

## Shared Code Handling

There are two main approaches to handling shared code in Docker:

### 1. Volume Mounting (Recommended for Development)

**How it works:**
- Shared code is mounted as a volume at runtime
- The host directory is mapped to a directory in the container
- Changes to shared code are immediately available to all services

**Implementation:**
- In `docker-compose.yml`:
  ```yaml
  services:
    my-service:
      volumes:
        - ./shared:/app/shared
  ```
- In `Dockerfile`:
  ```dockerfile
  # Shared modules are mounted as a volume
  ```

**Advantages:**
- No need to rebuild services when shared code changes
- Ensures all services use the same version of shared code
- Simplifies development workflow

**Example:**
See the `api-gateway` and `model-orchestration` services in this project.

### 2. Build-time Copying (Better for Production)

**How it works:**
- Shared code is copied into the Docker image during build
- Each service has its own copy of the shared code

**Implementation:**
- In `Dockerfile`:
  ```dockerfile
  COPY ./shared /app/shared
  ```

**Advantages for Production:**
- Images are self-contained and immutable
- No external dependencies at runtime
- More predictable behavior

**Disadvantages for Development:**
- Requires rebuilding all services when shared code changes
- May lead to inconsistencies if services use different versions
- Can cause Docker build context issues with parent directories

## Multi-Stage Builds

Use multi-stage builds to create smaller, more efficient images:

```dockerfile
# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy only what's needed from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY ./src /app/src

# Shared modules are mounted as a volume in development
# For production, uncomment the following line:
# COPY ./shared /app/shared

CMD ["python", "-m", "src.main"]
```

## Environment-Specific Configurations

Use different Docker Compose files for different environments:

### Development (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  api-gateway:
    build: ./services/api-gateway
    volumes:
      - ./shared:/app/shared
      - ./services/api-gateway/src:/app/src
    environment:
      - ENVIRONMENT=development
```

### Production (`docker-compose.prod.yml`)

```yaml
version: '3.8'

services:
  api-gateway:
    build:
      context: .
      dockerfile: ./services/api-gateway/Dockerfile.prod
    environment:
      - ENVIRONMENT=production
```

## Best Practices for Dockerfiles

### 1. Use Specific Base Images

Use specific versions of base images to ensure consistency:

```dockerfile
# Good
FROM python:3.11.4-slim

# Avoid
FROM python:latest
```

### 2. Minimize Layers

Combine related commands to reduce the number of layers:

```dockerfile
# Good
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Avoid
RUN apt-get update
RUN apt-get install -y --no-install-recommends gcc
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
```

### 3. Use .dockerignore

Create a `.dockerignore` file to exclude unnecessary files from the build context:

```
.git
.github
.vscode
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.coverage
htmlcov/
```

### 4. Set Non-Root User

Run containers as a non-root user for security:

```dockerfile
RUN useradd -m appuser
USER appuser
```

### 5. Use Environment Variables for Configuration

Use environment variables for configuration instead of hardcoding values:

```dockerfile
ENV APP_PORT=8000
ENV LOG_LEVEL=info

CMD ["python", "-m", "src.main"]
```

## Docker Compose Best Practices

### 1. Use Depends On

Use `depends_on` to specify service dependencies:

```yaml
services:
  api-gateway:
    depends_on:
      - postgres
      - redis
```

### 2. Use Health Checks

Add health checks to ensure services are ready:

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### 3. Use Named Volumes

Use named volumes for persistent data:

```yaml
services:
  postgres:
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

### 4. Use Networks

Use custom networks to control service communication:

```yaml
services:
  api-gateway:
    networks:
      - frontend
      - backend
  
  postgres:
    networks:
      - backend

networks:
  frontend:
  backend:
```

## Guidelines for Future Development

1. **Be consistent** in how shared dependencies are handled across services
   - All services should use the same approach
   - Prefer volume mounting for development environments
   - Use build-time copying for production environments

2. **Document** the approach in comments and documentation
   - Add clear comments in Dockerfiles
   - Update README files with setup instructions

3. **Test Docker builds** early and frequently
   - Verify both individual service builds and full docker-compose builds
   - Address issues before they compound

4. **Consider environment differences**
   - Development environments benefit from volume mounting
   - Production environments might prefer build-time copying for immutability

5. **Optimize for CI/CD**
   - Use build caching effectively
   - Consider using Docker BuildKit for faster builds
   - Implement proper tagging strategies

By following these guidelines, you'll avoid common pitfalls in multi-package Docker projects and ensure a smoother development experience.
