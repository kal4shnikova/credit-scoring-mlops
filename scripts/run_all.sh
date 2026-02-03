#!/bin/bash

# =============================================================================
# Script: Запуск полного ML Pipeline
# =============================================================================

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Получаем директорию проекта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Логотип
echo -e "${BLUE}"
cat << "EOF"
   ____ ____  _____ ____ ___ _____   ____   ____ ___  ____  ___ _   _  ____ 
  / ___|  _ \| ____|  _ \_ _|_   _| / ___| / ___/ _ \|  _ \|_ _| \ | |/ ___|
 | |   | |_) |  _| | | | | |  | |   \___ \| |  | | | | |_) || ||  \| | |  _ 
 | |___|  _ <| |___| |_| | |  | |    ___) | |__| |_| |  _ < | || |\  | |_| |
  \____|_| \_\_____|____/___| |_|   |____/ \____\___/|_| \_\___|_| \_|\____|
                                                                              
   __  __ _     ___  ____  ____    ____  ___ ____  _____ _     ___ _   _ _____ 
  |  \/  | |   / _ \|  _ \/ ___|  |  _ \|_ _|  _ \| ____| |   |_ _| \ | | ____|
  | |\/| | |  | | | | |_) \___ \  | |_) || || |_) |  _| | |    | ||  \| |  _|  
  | |  | | |__| |_| |  __/ ___) | |  __/ | ||  __/| |___| |___ | || |\  | |___ 
  |_|  |_|_____\___/|_|   |____/  |_|   |___|_|   |_____|_____|___|_| \_|_____|
                                                                                
EOF
echo -e "${NC}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Полный ML Pipeline${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Проверка виртуального окружения
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Виртуальное окружение не активировано${NC}"
    echo "Активируем автоматически..."
    source venv/bin/activate
    echo -e "${GREEN}✅ Активировано${NC}\n"
fi

# Счетчик времени
START_TIME=$(date +%s)

# Этап 1: Обучение модели
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Этап 1/5: Обучение модели${NC}"
echo -e "${BLUE}========================================${NC}\n"

./scripts/train_model.sh

echo -e "\n${GREEN}✅ Этап 1 завершен${NC}\n"
sleep 2

# Этап 2: Конвертация в ONNX
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Этап 2/5: Конвертация в ONNX${NC}"
echo -e "${BLUE}========================================${NC}\n"

./scripts/convert_onnx.sh

echo -e "\n${GREEN}✅ Этап 2 завершен${NC}\n"
sleep 2

# Этап 3: Оптимизация модели
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Этап 3/5: Оптимизация модели${NC}"
echo -e "${BLUE}========================================${NC}\n"

./scripts/optimize_model.sh

echo -e "\n${GREEN}✅ Этап 3 завершен${NC}\n"
sleep 2

# Этап 4: Мониторинг дрифта
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Этап 4/5: Мониторинг дрифта${NC}"
echo -e "${BLUE}========================================${NC}\n"

./scripts/check_drift.sh

echo -e "\n${GREEN}✅ Этап 4 завершен${NC}\n"
sleep 2

# Этап 5: Запуск и тестирование API
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Этап 5/5: Запуск и тестирование API${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}Запускаем API в фоновом режиме...${NC}"

# Запускаем API в фоне
./scripts/run_api.sh > logs/api_$(date +%Y%m%d_%H%M%S).log 2>&1 &
API_PID=$!

echo -e "${GREEN}✅ API запущен (PID: $API_PID)${NC}"
echo -e "${YELLOW}Ожидаем запуска сервера...${NC}\n"

# Ждем запуска API
sleep 10

# Проверяем доступность
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API доступен${NC}\n"
    
    # Запускаем тесты
    ./scripts/test_api.sh
    
else
    echo -e "${RED}❌ API недоступен${NC}"
    echo "Проверьте логи: tail logs/api_*.log"
fi

# Вычисляем время выполнения
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

# Итоговый отчет
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Все этапы завершены!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}📊 Итоги:${NC}\n"

# Размеры моделей
if [ -f "models/trained/credit_scoring_nn.pth" ]; then
    PYTORCH_SIZE=$(du -h models/trained/credit_scoring_nn.pth | cut -f1)
    echo -e "  PyTorch модель:         ${PYTORCH_SIZE}"
fi

if [ -f "models/onnx/credit_scoring_model.onnx" ]; then
    ONNX_SIZE=$(du -h models/onnx/credit_scoring_model.onnx | cut -f1)
    echo -e "  ONNX модель:            ${ONNX_SIZE}"
fi

if [ -f "models/optimization/credit_scoring_quantized.onnx" ]; then
    QUANTIZED_SIZE=$(du -h models/optimization/credit_scoring_quantized.onnx | cut -f1)
    echo -e "  Квантизованная модель:  ${QUANTIZED_SIZE}"
fi

echo -e "\n  Время выполнения:       ${MINUTES}м ${SECONDS}с"
echo -e "  API PID:                ${API_PID}"
echo ""

# Созданные файлы
echo -e "${BLUE}📁 Созданные файлы:${NC}"
echo -e "  models/trained/credit_scoring_nn.pth"
echo -e "  models/trained/scaler.pkl"
echo -e "  models/onnx/credit_scoring_model.onnx"
echo -e "  models/onnx/benchmark_results.json"
echo -e "  models/optimization/credit_scoring_quantized.onnx"
echo -e "  models/optimization/optimization_report.json"
echo -e "  monitoring/evidently/reports/*.html"
echo ""

# Endpoints
echo -e "${BLUE}🌐 API Endpoints:${NC}"
echo -e "  Health:      ${YELLOW}http://localhost:8000/health${NC}"
echo -e "  Docs:        ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  Predict:     ${YELLOW}http://localhost:8000/predict${NC}"
echo -e "  Metrics:     ${YELLOW}http://localhost:8000/metrics${NC}"
echo ""

# Следующие шаги
echo -e "${BLUE}📝 Следующие шаги:${NC}"
echo -e "  1. Откройте Swagger UI: ${YELLOW}open http://localhost:8000/docs${NC}"
echo -e "  2. Просмотрите отчеты о дрифте: ${YELLOW}open monitoring/evidently/reports/data_drift_report_*.html${NC}"
echo -e "  3. Сделайте скриншоты для документации"
echo -e "  4. Остановите API: ${YELLOW}kill $API_PID${NC}"
echo ""

echo -e "${GREEN}Готово! 🚀${NC}\n"
