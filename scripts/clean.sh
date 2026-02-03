#!/bin/bash

# =============================================================================
# Script: Очистка проекта
# =============================================================================

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Очистка проекта${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Получаем директорию проекта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo -e "${YELLOW}⚠️  Это удалит:${NC}"
echo "  - Обученные модели"
echo "  - ONNX модели"
echo "  - Оптимизированные модели"
echo "  - Логи"
echo "  - Отчеты о дрифте"
echo "  - Python cache"
echo ""

read -p "Продолжить? (y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Отменено${NC}"
    exit 0
fi

echo -e "\n${BLUE}🧹 Начинаем очистку...${NC}\n"

# Удаление моделей
if [ -d "models/trained" ]; then
    echo -e "${YELLOW}Удаление обученных моделей...${NC}"
    rm -rf models/trained/*
    echo -e "${GREEN}✅ Удалено${NC}"
fi

if [ -d "models/onnx" ]; then
    echo -e "${YELLOW}Удаление ONNX моделей...${NC}"
    rm -rf models/onnx/*
    echo -e "${GREEN}✅ Удалено${NC}"
fi

if [ -d "models/optimization" ]; then
    echo -e "${YELLOW}Удаление оптимизированных моделей...${NC}"
    rm -rf models/optimization/*
    echo -e "${GREEN}✅ Удалено${NC}"
fi

# Удаление логов
if [ -d "logs" ]; then
    echo -e "${YELLOW}Удаление логов...${NC}"
    rm -rf logs/*
    echo -e "${GREEN}✅ Удалено${NC}"
fi

# Удаление отчетов
if [ -d "monitoring/evidently/reports" ]; then
    echo -e "${YELLOW}Удаление отчетов о дрифте...${NC}"
    rm -rf monitoring/evidently/reports/*
    echo -e "${GREEN}✅ Удалено${NC}"
fi

if [ -d "monitoring/evidently/metrics" ]; then
    echo -e "${YELLOW}Удаление метрик дрифта...${NC}"
    rm -rf monitoring/evidently/metrics/*
    echo -e "${GREEN}✅ Удалено${NC}"
fi

# Удаление Python cache
echo -e "${YELLOW}Удаление Python cache...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
echo -e "${GREEN}✅ Удалено${NC}"

# Удаление .DS_Store (macOS)
echo -e "${YELLOW}Удаление .DS_Store файлов...${NC}"
find . -name ".DS_Store" -delete 2>/dev/null
echo -e "${GREEN}✅ Удалено${NC}"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Очистка завершена!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}Структура проекта сохранена.${NC}"
echo -e "${BLUE}Виртуальное окружение не удалено.${NC}\n"

echo -e "${YELLOW}Для полного удаления проекта:${NC}"
echo -e "  cd .. && rm -rf credit-scoring-mlops/\n"
