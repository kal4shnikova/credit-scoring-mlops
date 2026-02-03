#!/bin/bash

# =============================================================================
# Script: Конвертация модели в ONNX
# =============================================================================

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Конвертация модели в ONNX${NC}"
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

# Проверка наличия обученной модели
if [ ! -f "models/trained/credit_scoring_nn.pth" ]; then
    echo -e "${RED}❌ Обученная модель не найдена!${NC}"
    echo "Сначала запустите: ./scripts/train_model.sh"
    exit 1
fi

# Создаем необходимые директории
mkdir -p models/onnx
mkdir -p logs

# Запускаем конвертацию
echo -e "${BLUE}🔄 Начинаем конвертацию в ONNX...${NC}\n"

python3 models/onnx/convert_to_onnx.py 2>&1 | tee logs/onnx_conversion_$(date +%Y%m%d_%H%M%S).log

# Проверяем результат
if [ -f "models/onnx/credit_scoring_model.onnx" ]; then
    echo -e "\n${GREEN}✅ Конвертация успешно завершена!${NC}"
    echo -e "${GREEN}📁 ONNX модель сохранена в: models/onnx/${NC}\n"
    
    # Показываем размеры моделей
    PYTORCH_SIZE=$(du -h models/trained/credit_scoring_nn.pth | cut -f1)
    ONNX_SIZE=$(du -h models/onnx/credit_scoring_model.onnx | cut -f1)
    
    echo -e "${BLUE}📊 Сравнение размеров:${NC}"
    echo -e "  PyTorch: ${PYTORCH_SIZE}"
    echo -e "  ONNX:    ${ONNX_SIZE}\n"
    
    # Показываем benchmark результаты если есть
    if [ -f "models/onnx/benchmark_results.json" ]; then
        echo -e "${BLUE}📈 Результаты benchmark:${NC}"
        python3 -c "
import json
with open('models/onnx/benchmark_results.json') as f:
    data = json.load(f)
    print(f\"  PyTorch: {data['pytorch_mean_ms']:.4f} ms\")
    print(f\"  ONNX:    {data['onnx_mean_ms']:.4f} ms\")
    print(f\"  Ускорение: {data['speedup']:.2f}x\")
" 2>/dev/null || echo "  (данные недоступны)"
    fi
    
    echo -e "\n${BLUE}Следующий шаг:${NC}"
    echo -e "  Запустите: ${YELLOW}./scripts/optimize_model.sh${NC}\n"
else
    echo -e "\n${RED}❌ Ошибка при конвертации${NC}"
    echo "Проверьте логи в директории logs/"
    exit 1
fi
