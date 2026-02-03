#!/bin/bash

# =============================================================================
# Script: Мониторинг дрифта с Evidently AI
# =============================================================================

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Мониторинг дрифта данных${NC}"
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

# Проверка установки Evidently
python3 -c "import evidently" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Установка Evidently AI...${NC}"
    pip install evidently
fi

# Создаем необходимые директории
mkdir -p monitoring/evidently/{reports,metrics}
mkdir -p logs

# Запускаем мониторинг дрифта
echo -e "${BLUE}🔍 Анализируем дрифт данных...${NC}\n"

python3 monitoring/evidently/drift_detection.py 2>&1 | tee logs/drift_monitoring_$(date +%Y%m%d_%H%M%S).log

# Проверяем результаты
if [ -d "monitoring/evidently/reports" ]; then
    REPORT_COUNT=$(find monitoring/evidently/reports -name "*.html" | wc -l | tr -d ' ')
    
    if [ "$REPORT_COUNT" -gt 0 ]; then
        echo -e "\n${GREEN}✅ Отчеты о дрифте созданы!${NC}"
        echo -e "${GREEN}📁 Найдено отчетов: ${REPORT_COUNT}${NC}\n"
        
        # Показываем список отчетов
        echo -e "${BLUE}📊 Созданные отчеты:${NC}"
        find monitoring/evidently/reports -name "*.html" -type f -exec basename {} \; | sort | tail -5 | while read report; do
            echo -e "  - ${YELLOW}$report${NC}"
        done
        echo ""
        
        # Находим последний отчет о дрифте данных
        LATEST_REPORT=$(find monitoring/evidently/reports -name "data_drift_report_*.html" -type f | sort | tail -1)
        
        if [ -n "$LATEST_REPORT" ]; then
            echo -e "${BLUE}📈 Последний отчет о дрифте:${NC}"
            echo -e "  ${YELLOW}$LATEST_REPORT${NC}\n"
            
            # Открываем отчет в браузере
            echo -e "${BLUE}🌐 Открываем отчет в браузере...${NC}"
            open "$LATEST_REPORT" 2>/dev/null || echo -e "${YELLOW}Откройте вручную: open $LATEST_REPORT${NC}"
        fi
        
        # Проверяем метрики
        if [ -f "monitoring/evidently/metrics/drift_metrics.json" ]; then
            echo -e "\n${BLUE}📊 Метрики дрифта:${NC}"
            python3 -c "
import json
with open('monitoring/evidently/metrics/drift_metrics.json') as f:
    data = json.load(f)
    drift_score = data.get('dataset_drift_score', 0)
    n_drifted = data.get('number_of_drifted_columns', 0)
    n_total = data.get('number_of_columns', 0)
    
    print(f\"  Drift Score: {drift_score:.2%}\")
    print(f\"  Drifted Columns: {n_drifted}/{n_total}\")
    
    # Предупреждение если дрифт высокий
    if drift_score > 0.3:
        print(f\"  ⚠️  ВНИМАНИЕ: Обнаружен значительный дрифт!\")
        print(f\"  💡 Рекомендуется переобучение модели\")
" 2>/dev/null
        fi
        
    else
        echo -e "\n${YELLOW}⚠️  Отчеты не найдены${NC}"
    fi
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Мониторинг дрифта завершен${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}💡 Полезные команды:${NC}"
echo -e "  Просмотр всех отчетов:   ${YELLOW}open monitoring/evidently/reports/${NC}"
echo -e "  Последний отчет:         ${YELLOW}open monitoring/evidently/reports/data_drift_report_*.html${NC}"
echo ""
