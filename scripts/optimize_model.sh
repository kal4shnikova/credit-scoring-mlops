#!/bin/bash

# =============================================================================
# Script: Оптимизация модели (Quantization)
# =============================================================================

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Оптимизация модели (Quantization)${NC}"
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

# Проверка наличия ONNX модели
if [ ! -f "models/onnx/credit_scoring_model.onnx" ]; then
    echo -e "${RED}❌ ONNX модель не найдена!${NC}"
    echo "Сначала запустите: ./scripts/convert_onnx.sh"
    exit 1
fi

# Создаем необходимые директории
mkdir -p models/optimization
mkdir -p logs

# Запускаем оптимизацию
echo -e "${BLUE}🔧 Начинаем квантизацию модели...${NC}\n"

python3 models/optimization/quantize.py 2>&1 | tee logs/optimization_$(date +%Y%m%d_%H%M%S).log

# Проверяем результат
if [ -f "models/optimization/credit_scoring_quantized.onnx" ]; then
    echo -e "\n${GREEN}✅ Оптимизация успешно завершена!${NC}"
    echo -e "${GREEN}📁 Квантизованная модель сохранена в: models/optimization/${NC}\n"
    
    # Показываем размеры моделей
    ORIGINAL_SIZE=$(du -h models/onnx/credit_scoring_model.onnx | cut -f1)
    QUANTIZED_SIZE=$(du -h models/optimization/credit_scoring_quantized.onnx | cut -f1)
    
    echo -e "${BLUE}📊 Сравнение размеров:${NC}"
    echo -e "  Оригинал:     ${ORIGINAL_SIZE}"
    echo -e "  Квантизация:  ${QUANTIZED_SIZE}\n"
    
    # Показываем отчет об оптимизации если есть
    if [ -f "models/optimization/optimization_report.json" ]; then
        echo -e "${BLUE}📈 Результаты оптимизации:${NC}"
        python3 -c "
import json
with open('models/optimization/optimization_report.json') as f:
    data = json.load(f)
    print(f\"  Уменьшение размера: {data['size_reduction']['reduction_percent']:.1f}%\")
    print(f\"  Ускорение: {data['performance']['speedup']:.2f}x\")
    print(f\"  Корреляция точности: {data['accuracy']['correlation']:.4f}\")
" 2>/dev/null || echo "  (данные недоступны)"
    fi
    
    echo -e "\n${BLUE}Следующий шаг:${NC}"
    echo -e "  Запустите API: ${YELLOW}./scripts/run_api.sh${NC}\n"
else
    echo -e "\n${RED}❌ Ошибка при оптимизации${NC}"
    echo "Проверьте логи в директории logs/"
    exit 1
fi
