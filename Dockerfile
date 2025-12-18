# =============================================================================
# Professional Insulation Estimation System
# Cloud Run Optimized Multi-Stage Dockerfile
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and compile wheels
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/build/wheels -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Cloud Run uses PORT env var (defaults to 8501 for local dev)
    PORT=8501 \
    # Application defaults (overridden by environment)
    CACHE_BACKEND=file \
    STORAGE_BACKEND=local \
    LOG_LEVEL=INFO

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    # For pdf2image / poppler
    poppler-utils \
    # For healthcheck
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application files
# Core estimation modules
COPY --chown=appuser:appgroup streamlit_app.py .
COPY --chown=appuser:appgroup agent_estimation_app.py .
COPY --chown=appuser:appgroup hvac_insulation_estimator.py .
COPY --chown=appuser:appgroup claude_estimation_agent.py .
COPY --chown=appuser:appgroup claude_agent_tools.py .

# Utility modules
COPY --chown=appuser:appgroup utils_cache.py .
COPY --chown=appuser:appgroup utils_async.py .
COPY --chown=appuser:appgroup utils_tracking.py .
COPY --chown=appuser:appgroup utils_pdf.py .
COPY --chown=appuser:appgroup pydantic_models.py .
COPY --chown=appuser:appgroup errors.py .

# GCP integration modules (new)
COPY --chown=appuser:appgroup cloud_config.py .
COPY --chown=appuser:appgroup gcs_storage.py .
COPY --chown=appuser:appgroup firestore_cache.py .
COPY --chown=appuser:appgroup secrets_manager.py .

# Legacy/alternative modules
COPY --chown=appuser:appgroup gemini_pdf_extractor.py .

# Data files
COPY --chown=appuser:appgroup pricebook_sample.json .
COPY --chown=appuser:appgroup measurements_template.csv .

# Streamlit configuration
COPY --chown=appuser:appgroup .streamlit/ .streamlit/

# Create cache directory with proper permissions
RUN mkdir -p /app/.cache && chown -R appuser:appgroup /app/.cache

# Switch to non-root user
USER appuser

# Expose port (Cloud Run will override with $PORT)
EXPOSE ${PORT}

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:${PORT}/_stcore/health || exit 1

# Entrypoint script to support $PORT environment variable
# Cloud Run sets PORT, local development uses default 8501
CMD sh -c 'streamlit run agent_estimation_app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true \
    --browser.gatherUsageStats=false'
