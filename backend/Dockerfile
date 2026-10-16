# API do Cali Burger (FastAPI + Uvicorn)
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN pip install .

COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts

# Usuário sem privilégios; a pasta de mídia recebe as imagens enviadas.
RUN useradd --create-home --uid 1000 caliburger \
    && mkdir -p /app/media \
    && chown -R caliburger /app/media
USER caliburger

ENV MEDIA_DIR=/app/media
EXPOSE 8000

# Aplica as migrações pendentes e sobe a API (atrás do Nginx, que repassa o IP do cliente).
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
