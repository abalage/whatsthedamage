FROM python:3.13-slim-trixie

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

# Expose port 5000
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/bin/curl -f http://localhost:5000/health || exit 1

# Entrypoint to start Flask server in production mode using Gunicorn
CMD ["gunicorn", "--config", "gunicorn_conf.py", "whatsthedamage.app:app"]