# Council Agent System - Production Dockerfile
# Multi-stage build for optimized image size and security
#
# Build: docker build -t cesi-council:latest .
# Run:   docker run --rm -it cesi-council:latest

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir chromadb

# ============================================================================
# Stage 2: Production - Minimal runtime image
# ============================================================================
FROM python:3.12-slim AS production

# Security: Create non-root user
RUN groupadd -r council && useradd -r -g council council

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=council:council . .

# Create necessary directories
RUN mkdir -p /app/.council /app/.ptc_output && \
    chown -R council:council /app

# Switch to non-root user
USER council

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PTC_OUTPUT_DIR=/app/.ptc_output

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "-m", "council"]

# ============================================================================
# Stage 3: PTC Sandbox - Isolated execution environment
# ============================================================================
FROM python:3.12-slim AS ptc-sandbox

# Security: Create non-root user
RUN groupadd -r ptc && useradd -r -g ptc ptc

WORKDIR /sandbox

# Create output directory
RUN mkdir -p /sandbox/output && chown -R ptc:ptc /sandbox

# Copy PTC SDK
COPY --chown=ptc:ptc scripts/ptc_sdk.py /sandbox/ptc_sdk.py

# Switch to non-root user
USER ptc

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PTC_OUTPUT_DIR=/sandbox/output

# Default command
CMD ["python", "agent_script.py"]

# ============================================================================
# Stage 4: Development - Full development environment
# ============================================================================
FROM python:3.12-slim AS development

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install all dependencies including dev
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev,distributed]" || pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port for dashboard
EXPOSE 8080

# Default command for development
CMD ["python", "run_dashboard.py"]
