#!/bin/bash

# =============================================================================
# Script: Тестирование API
# =============================================================================

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Тестирование Credit Scoring API${NC}"
echo -e "${BLUE}========================================${NC}\n"

API_URL="${1:-http://localhost:8000}"

echo -e "${BLUE}API URL: ${API_URL}${NC}\n"

# Функция для теста endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -e "${BLUE}🧪 Тестируем: ${name}${NC}"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" == "200" ]; then
        echo -e "${GREEN}✅ Успешно (HTTP $http_code)${NC}"
        echo -e "${YELLOW}Ответ:${NC} ${body:0:100}...\n"
    else
        echo -e "${RED}❌ Ошибка (HTTP $http_code)${NC}"
        echo -e "${YELLOW}Ответ:${NC} $body\n"
    fi
}

# Проверка доступности API
echo -e "${BLUE}🔍 Проверка доступности API...${NC}\n"

if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ API недоступен по адресу: $API_URL${NC}"
    echo -e "${YELLOW}Убедитесь, что API запущен: ./scripts/run_api.sh${NC}\n"
    exit 1
fi

echo -e "${GREEN}✅ API доступен${NC}\n"

# Тест 1: Health Check
test_endpoint "Health Check" "GET" "/health"

# Тест 2: Root Endpoint
test_endpoint "Root Endpoint" "GET" "/"

# Тест 3: Model Info
test_endpoint "Model Info" "GET" "/model/info"

# Тест 4: Single Prediction - Low Risk
echo -e "${BLUE}🧪 Тестируем: Предсказание (низкий риск)${NC}"
LOW_RISK_DATA='{
    "age": 45,
    "income": 100000,
    "loan_amount": 10000,
    "credit_history_length": 20,
    "num_open_accounts": 5,
    "debt_to_income": 0.2,
    "num_late_payments": 0,
    "employment_length": 15,
    "num_credit_inquiries": 1,
    "credit_utilization": 0.3
}'

response=$(curl -s -X POST "$API_URL/predict" \
    -H "Content-Type: application/json" \
    -d "$LOW_RISK_DATA")

echo -e "${GREEN}✅ Успешно${NC}"
echo -e "${YELLOW}Ответ:${NC}"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Тест 5: Single Prediction - High Risk
echo -e "${BLUE}🧪 Тестируем: Предсказание (высокий риск)${NC}"
HIGH_RISK_DATA='{
    "age": 22,
    "income": 25000,
    "loan_amount": 50000,
    "credit_history_length": 1,
    "num_open_accounts": 10,
    "debt_to_income": 0.8,
    "num_late_payments": 5,
    "employment_length": 1,
    "num_credit_inquiries": 8,
    "credit_utilization": 0.95
}'

response=$(curl -s -X POST "$API_URL/predict" \
    -H "Content-Type: application/json" \
    -d "$HIGH_RISK_DATA")

echo -e "${GREEN}✅ Успешно${NC}"
echo -e "${YELLOW}Ответ:${NC}"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Тест 6: Batch Prediction
echo -e "${BLUE}🧪 Тестируем: Batch Prediction${NC}"
BATCH_DATA='{
    "applications": [
        {
            "age": 35,
            "income": 60000,
            "loan_amount": 15000,
            "credit_history_length": 10,
            "num_open_accounts": 5,
            "debt_to_income": 0.3,
            "num_late_payments": 0,
            "employment_length": 8,
            "num_credit_inquiries": 2,
            "credit_utilization": 0.4
        },
        {
            "age": 28,
            "income": 45000,
            "loan_amount": 20000,
            "credit_history_length": 5,
            "num_open_accounts": 7,
            "debt_to_income": 0.5,
            "num_late_payments": 1,
            "employment_length": 4,
            "num_credit_inquiries": 3,
            "credit_utilization": 0.6
        }
    ]
}'

response=$(curl -s -X POST "$API_URL/predict/batch" \
    -H "Content-Type: application/json" \
    -d "$BATCH_DATA")

echo -e "${GREEN}✅ Успешно${NC}"
echo -e "${YELLOW}Batch size:${NC} $(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['batch_size'])" 2>/dev/null || echo "N/A")"
echo ""

# Тест 7: Prometheus Metrics
echo -e "${BLUE}🧪 Тестируем: Prometheus Metrics${NC}"
metrics=$(curl -s "$API_URL/metrics")

if echo "$metrics" | grep -q "credit_scoring"; then
    echo -e "${GREEN}✅ Метрики доступны${NC}"
    echo -e "${YELLOW}Пример метрик:${NC}"
    echo "$metrics" | grep "credit_scoring" | head -5
    echo ""
else
    echo -e "${RED}❌ Метрики недоступны${NC}\n"
fi

# Тест 8: Invalid Request
echo -e "${BLUE}🧪 Тестируем: Invalid Request (должен вернуть 422)${NC}"
INVALID_DATA='{"age": 150}'  # Невалидные данные

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/predict" \
    -H "Content-Type: application/json" \
    -d "$INVALID_DATA")

http_code=$(echo "$response" | tail -n1)

if [ "$http_code" == "422" ]; then
    echo -e "${GREEN}✅ Корректно обработан невалидный запрос (HTTP 422)${NC}\n"
else
    echo -e "${RED}❌ Неожиданный код: HTTP $http_code${NC}\n"
fi

# Итоги
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Все тесты завершены!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}Дополнительные команды:${NC}"
echo -e "  Swagger UI:  ${YELLOW}open $API_URL/docs${NC}"
echo -e "  ReDoc:       ${YELLOW}open $API_URL/redoc${NC}"
echo ""
