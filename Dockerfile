# syntax=docker/dockerfile:1

FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN addgroup --system --gid 10001 appgroup \
    && adduser --system --uid 10001 --ingroup appgroup app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY server ./server
COPY rag ./rag
COPY main.py ./main.py

USER 10001

EXPOSE 8000

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]