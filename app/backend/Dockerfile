FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Ставим системные зависимости (минимум)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Сначала зависимости — чтобы docker build кешировался
COPY app/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Затем — код приложения
COPY app/backend/ .

# Создаём нерутового пользователя
RUN useradd -m appuser
USER appuser

EXPOSE 8000

ENV APP_ENV=container

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
