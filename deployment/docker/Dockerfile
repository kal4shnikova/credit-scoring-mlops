# Multi-stage Dockerfile для Credit Scoring API
# Оптимизированный для production использования

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.9-slim as builder

WORKDIR /build

# Установка системных зависимостей для компиляции
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей в отдельную директорию
RUN pip install --user --no-cache-dir --no-warn-script-location \
    -r requirements.txt

# ============================================
# Stage 2: DVC (Data Version Control)
# ============================================
FROM python:3.9-slim as dvc

WORKDIR /app

# Установка git и DVC
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir dvc[s3]

# Копирование конфигурации DVC
COPY .dvc ./.dvc
COPY .dvcignore .

# Копирование данных и моделей (если используется DVC)
# В реальном проекте модели будут загружаться из S3
COPY models ./models
COPY data ./data

# Загрузка данных из DVC remote (если настроено)
# RUN dvc pull -R

# ============================================
# Stage 3: Final Production Image
# ============================================
FROM python:3.9-slim

# Метаданные
LABEL maintainer="your-email@example.com"
LABEL version="1.0"
LABEL description="Credit Scoring ML API"

# Создание непривилегированного пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Копирование Python зависимостей из builder
COPY --from=builder /root/.local /root/.local

# Копирование моделей и данных из DVC stage
COPY --from=dvc /app/models ./models
COPY --from=dvc /app/data ./data

# Копирование исходного кода приложения
COPY api/ ./api/
COPY config/ ./config/

# Создание директорий для логов и кеша
RUN mkdir -p /app/logs /app/cache && \
    chown -R appuser:appuser /app

# Настройка PATH для локальных Python packages
ENV PATH=/root/.local/bin:$PATH

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_PATH=/app/models/optimization/credit_scoring_quantized.onnx \
    SCALER_PATH=/app/models/trained/scaler.pkl \
    LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Переключение на непривилегированного пользователя
USER appuser

# Expose порт
EXPOSE 8000

# Запуск приложения с Uvicorn
CMD ["uvicorn", "api.app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info", \
     "--access-log", \
     "--no-use-colors"]

# Альтернативный запуск с Gunicorn (для высоких нагрузок)
# CMD ["gunicorn", "api.app.main:app", \
#      "--bind", "0.0.0.0:8000", \
#      "--workers", "4", \
#      "--worker-class", "uvicorn.workers.UvicornWorker", \
#      "--access-logfile", "-", \
#      "--error-logfile", "-", \
#      "--log-level", "info"]
