# Multi-stage Docker build for whatsthedamage
# Stage 1: Build frontend production assets
FROM node:24-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend dependency files
COPY frontend/package.json frontend/package-lock.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source files
COPY frontend/ ./

# Build frontend for production (sets VITE_API_BASE_URL=/api/v2)
RUN npm run build:prod

# =============================================================================
# Stage 2: Build backend Python dependencies
FROM python:3.13-slim-trixie AS backend-builder

# Accept version as build argument
ARG VERSION=dev
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_WHATSTHEDAMAGE=$VERSION
ENV USER=appuser

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (including curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    file \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with home directory
RUN groupadd -r ${USER} && useradd -r -g ${USER} -m ${USER}

# Create app directory and set ownership
RUN mkdir /app && chown -R ${USER}:${USER} /app

# Set working directory
WORKDIR /app

# Copy dependency files as root first
COPY pyproject.toml requirements.txt requirements-web.txt ./

# Install Python dependencies as root (system-wide)
RUN pip install --no-cache-dir -r requirements.txt -r requirements-web.txt

# Copy the application code
COPY . .

# Fix ownership of all copied files
RUN chown -R ${USER}:${USER} /app

# Switch to non-root user
USER ${USER}

# Add local bin to PATH for appuser
ENV PATH="/home/${USER}/.local/bin:${PATH}"

# Install the package in editable mode
RUN pip install --no-cache-dir --no-deps --user -e .

# =============================================================================
# Stage 3: Production image (runtime only)
FROM python:3.13-slim-trixie

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV USER=appuser

# Install runtime system dependencies (file for MIME type detection)
RUN apt-get update && apt-get install -y --no-install-recommends \
    file \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with home directory
RUN groupadd -r ${USER} && useradd -r -g ${USER} -m ${USER}

# Create app directory and set ownership
RUN mkdir /app && chown -R ${USER}:${USER} /app

# Set working directory
WORKDIR /app

# Copy Python dependencies from backend-builder
COPY --from=backend-builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /home/appuser/.local /home/appuser/.local

# Copy backend code from backend-builder
COPY --from=backend-builder /app /app

# Copy frontend build output to Flask static directory
COPY --from=frontend-builder /app/frontend/dist /app/src/whatsthedamage/view/static/dist

# Ensure proper ownership
RUN chown -R ${USER}:${USER} /app

# Switch to non-root user
USER ${USER}

# Add local bin and python bin to PATH for appuser
ENV PATH="/home/${USER}/.local/bin:/usr/local/bin:${PATH}"

# Expose port 5000
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/bin/curl -f http://localhost:5000/health || exit 1

# Entrypoint to start Flask server in production mode using Gunicorn
CMD ["gunicorn", "--config", "config/gunicorn_conf.py", "whatsthedamage.app:app"]
