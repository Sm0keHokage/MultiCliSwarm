# Use official Python slim image for a smaller footprint
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    STORAGE_DIR=/data

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and data directory
RUN useradd -m swarmuser && mkdir -p /data && chown swarmuser:swarmuser /data
USER swarmuser
WORKDIR /home/swarmuser/app

# Copy dependency files and install
COPY --chown=swarmuser:swarmuser pyproject.toml setup.py ./
RUN pip install --no-cache-dir -e .

# Copy source code
COPY --chown=swarmuser:swarmuser src/ ./src/
COPY --chown=swarmuser:swarmuser README.md ./

# Expose ports for UI, MCP, and Bridge
EXPOSE 8080 8000 9999

# Healthcheck to ensure the UI is up
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/ || exit 1

# Start the Web UI by default
CMD ["multicliswarm-ui"]
