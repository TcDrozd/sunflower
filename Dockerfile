FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update -y && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt /app/
RUN pip install -r requirements.txt

COPY app/ /app/

# Gunicorn defaults: 2-4 workers is fine for small apps; tweak later if needed.
# Bind to 0.0.0.0 so the reverse proxy can reach it
CMD ["gunicorn", "--workers", "3", "--threads", "2", "--timeout", "60", "-b", "0.0.0.0:8000", "wsgi:app"]