FROM python:3.13-trixie

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (including curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Create app directory and set ownership
RUN mkdir /app && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies with --user flag
RUN pip install --user --no-cache-dir --upgrade pip \
    && pip install --user --no-cache-dir -r requirements.txt \
    && pip install --user --no-cache-dir gunicorn

# Add user's local bin to PATH
ENV PATH="/home/appuser/.local/bin:$PATH"

# Copy the application code
COPY . .

# Install the package in editable mode
RUN pip install --user -e .

# Expose port 5000
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Entrypoint to start Flask server in production mode using Gunicorn
CMD ["gunicorn", "--config", "gunicorn_conf.py", "whatsthedamage.app:app"]