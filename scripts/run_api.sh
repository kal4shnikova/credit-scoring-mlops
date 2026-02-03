#!/bin/bash

# =============================================================================
# Script: Запуск FastAPI приложения
# =============================================================================

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Запуск Credit Scoring API${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Получаем директорию проекта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Проверка виртуального окружения
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Виртуальное окружение не активировано${NC}"
    echo "Активируем автоматически..."
    source venv/bin/activate
fi

# Проверка наличия оптимизированной модели
if [ ! -f "models/optimization/credit_scoring_quantized.onnx" ]; then
    echo -e "${YELLOW}⚠️  Оптимизированная модель не найдена${NC}"
    echo "Попытка использовать ONNX модель..."
    
    if [ ! -f "models/onnx/credit_scoring_model.onnx" ]; then
        echo -e "${RED}❌ ONNX модель не найдена!${NC}"
        echo "Сначала запустите: ./scripts/train_model.sh && ./scripts/convert_onnx.sh"
        exit 1
    fi
    
    # Копируем ONNX модель в optimization для API
    mkdir -p models/optimization
    cp models/onnx/credit_scoring_model.onnx models/optimization/credit_scoring_quantized.onnx
    echo -e "${GREEN}✅ Скопирована ONNX модель${NC}"
fi

# Проверка наличия FastAPI зависимостей
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Установка FastAPI зависимостей...${NC}"
    pip install fastapi uvicorn pydantic prometheus-client
fi

# Настройка переменных окружения
export MODEL_PATH="$PROJECT_ROOT/models/optimization/credit_scoring_quantized.onnx"
export SCALER_PATH="$PROJECT_ROOT/models/trained/scaler.pkl"
export LOG_LEVEL="INFO"

echo -e "${BLUE}📋 Конфигурация:${NC}"
echo -e "  Model: $MODEL_PATH"
echo -e "  Scaler: $SCALER_PATH"
echo -e "  Log Level: $LOG_LEVEL\n"

# Создаем директорию для логов
mkdir -p logs

echo -e "${GREEN}🚀 Запуск API сервера...${NC}\n"
echo -e "${BLUE}Доступные endpoints:${NC}"
echo -e "  Health:      ${YELLOW}http://localhost:8000/health${NC}"
echo -e "  Docs:        ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  Predict:     ${YELLOW}http://localhost:8000/predict${NC}"
echo -e "  Metrics:     ${YELLOW}http://localhost:8000/metrics${NC}\n"

echo -e "${BLUE}Для остановки нажмите Ctrl+C${NC}\n"
echo -e "${BLUE}========================================${NC}\n"

# Запускаем API
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
