FROM python:3.13-slim AS base

# Environment hygiene
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    FLASK_APP=timeclock.py

# System deps required for building wheels and rendering (WeasyPrint/Cairo, etc.)
RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      build-essential \
      libffi-dev \
      libpq-dev \
      libcairo2 \
      libgdk-pixbuf-2.0-0 \
      libpango-1.0-0 \
      libpangocairo-1.0-0 \
      libpangoft2-1.0-0 \
      libjpeg62-turbo \
      zlib1g \
      fonts-dejavu-core \
      curl \
      ca-certificates; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Pipenv dependencies from lock file (deterministic build)
COPY Pipfile Pipfile.lock ./
RUN python -m pip install --upgrade --no-cache-dir pip pipenv && \
    PIPENV_YES=1 PIPENV_VENV_IN_PROJECT=0 pipenv install --deploy --system

# Copy application (only what is needed to run)
COPY app ./app
COPY timeclock.py config.py Procfile ./
COPY migrations ./migrations
COPY docker-entrypoint.sh ./

# Create non-root user
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app/docker-entrypoint.sh
USER appuser

EXPOSE 5000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "timeclock:app"]
