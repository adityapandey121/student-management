# Small official Python image; "slim" drops compilers and docs we don't need.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=5000

WORKDIR /app

# Install dependencies first so this layer is cached when only code changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Run as an unprivileged user instead of root.
RUN useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser app.py storage.py main.py ./

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=2)"

# Shell form so $PORT is expanded; exec makes gunicorn PID 1 and receive signals.
# One worker + threads: in-memory storage must be shared by all requests.
CMD exec gunicorn --bind "0.0.0.0:${PORT}" --workers 1 --threads 4 --access-logfile - "app:create_app()"
