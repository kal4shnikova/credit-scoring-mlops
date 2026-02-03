# Credit Scoring MLOps Pipeline

Промышленное развертывание кредитной скоринговой системы с полным MLOps-циклом

## 📋 Описание проекта

Этот проект представляет собой полноценную систему машинного обучения для кредитного скоринга с автоматизированной доставкой моделей, мониторингом и управлением жизненным циклом.

## 🏗️ Архитектура

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   GitHub    │───▶│  CI/CD       │───▶│  Kubernetes │
│   Actions   │    │  Pipeline    │    │   Cluster   │
└─────────────┘    └──────────────┘    └─────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │  Monitoring  │
                   │  & Alerting  │
                   └──────────────┘
```

## 📂 Структура проекта

```
.
├── .github/workflows/        # CI/CD пайплайны
│   ├── ci-cd.yml            # Основной пайплайн
│   ├── build-staging.yml    # Деплой в staging
│   └── deploy-production.yml# Деплой в production
├── infrastructure/          # Terraform конфигурация
│   ├── modules/
│   │   ├── network/        # VPC, подсети
│   │   ├── kubernetes/     # Managed K8s кластер
│   │   ├── storage/        # Object Storage
│   │   └── monitoring/     # Prometheus, Grafana
│   └── environments/
│       ├── staging/        # Staging окружение
│       └── production/     # Production окружение
├── models/                  # ML модели
│   ├── training/           # Обучение моделей
│   ├── onnx/              # ONNX конвертация
│   └── optimization/       # Оптимизация (quantization, pruning)
├── api/                     # FastAPI приложение
│   └── app/
│       ├── main.py         # Основное приложение
│       ├── models.py       # Pydantic модели
│       └── routers/        # API endpoints
├── deployment/              # Конфигурация развертывания
│   ├── kubernetes/         # K8s манифесты
│   └── docker/            # Dockerfile
├── monitoring/              # Мониторинг
│   ├── prometheus/         # Метрики
│   ├── grafana/           # Дашборды
│   └── evidently/         # Мониторинг дрифта
├── airflow/                 # Автоматизация
│   └── dags/              # DAG для переобучения
└── notebooks/               # Jupyter ноутбуки для анализа
```

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.9+
- Docker & Docker Compose
- Terraform 1.0+
- kubectl
- Доступ к облачному провайдеру (Yandex Cloud/VK Cloud/Selectel)

### Установка

1. **Клонирование репозитория**
```bash
git clone https://github.com/your-username/credit-scoring-mlops.git
cd credit-scoring-mlops
```

2. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

3. **Настройка переменных окружения**
```bash
cp .env.example .env
# Отредактируйте .env с вашими настройками
```

4. **Обучение модели**
```bash
python models/training/train_nn.py
```

5. **Конвертация в ONNX**
```bash
python models/onnx/convert_to_onnx.py
```

## 📊 Этапы проекта

### ✅ Этап 1: Подготовка модели

- [x] Создание нейронной сети
- [x] Конвертация в ONNX
- [x] Сравнение производительности
- [x] Оптимизация (quantization/pruning)
- [x] Нагрузочное тестирование

**Файлы:**
- `models/training/train_nn.py` - обучение модели
- `models/onnx/convert_to_onnx.py` - конвертация в ONNX
- `models/optimization/quantize.py` - квантизация
- `models/optimization/benchmark.py` - бенчмарки

### ✅ Этап 2: Cloud Infrastructure

- [x] Terraform конфигурация
- [x] Модульная структура
- [x] Remote state в Object Storage
- [x] Managed Kubernetes кластер

**Файлы:**
- `infrastructure/modules/kubernetes/main.tf`
- `infrastructure/environments/production/main.tf`

### ✅ Этап 3: Контейнеризация

- [x] Multi-stage Dockerfile
- [x] Kubernetes манифесты
- [x] Auto-scaling конфигурация

**Файлы:**
- `deployment/docker/Dockerfile`
- `deployment/kubernetes/deployment.yaml`

### ✅ Этап 4: CI/CD Pipeline

- [x] GitHub Actions workflow
- [x] Multi-stage pipeline
- [x] Security scanning
- [x] Auto-deployment

**Файлы:**
- `.github/workflows/ci-cd.yml`

### ✅ Этап 5: Мониторинг

- [x] Prometheus метрики
- [x] Grafana дашборды
- [x] Alerting правила

**Файлы:**
- `monitoring/prometheus/prometheus.yml`
- `monitoring/grafana/dashboards/`

### ✅ Этап 6: Мониторинг дрифта

- [x] Evidently AI интеграция
- [x] Data drift мониторинг
- [x] Model performance tracking

**Файлы:**
- `monitoring/evidently/drift_detection.py`

### ✅ Этап 7: Автоматизация

- [x] Airflow DAG для переобучения
- [x] Триггеры по дрифту
- [x] Автоматическое тестирование

**Файлы:**
- `airflow/dags/retraining_dag.py`

## 🔧 Локальная разработка

### Запуск API локально

```bash
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступен по адресу: http://localhost:8000
Документация Swagger: http://localhost:8000/docs

### Запуск с Docker Compose

```bash
docker-compose up -d
```

Это запустит:
- API сервис (порт 8000)
- Prometheus (порт 9090)
- Grafana (порт 3000)

## ☁️ Развертывание в облаке

### 1. Инициализация Terraform

```bash
cd infrastructure/environments/production
terraform init
terraform plan
terraform apply
```

### 2. Настройка kubectl

```bash
# Для Yandex Cloud
yc managed-kubernetes cluster get-credentials <cluster-name> --external

# Проверка подключения
kubectl get nodes
```

### 3. Деплой приложения

```bash
kubectl apply -f deployment/kubernetes/
```

### 4. Проверка статуса

```bash
kubectl get pods -n default
kubectl get svc -n default
```

## 📈 Мониторинг

### Grafana Dashboard

1. Откройте Grafana: http://<LOAD_BALANCER_IP>:3000
2. Логин/пароль: admin/admin
3. Импортируйте дашборды из `monitoring/grafana/dashboards/`

### Prometheus

Метрики доступны по адресу: http://<PROMETHEUS_IP>:9090

### Evidently Reports

HTML отчеты генерируются в `monitoring/evidently/reports/`

## 🧪 Тестирование

```bash
# Юнит-тесты
pytest tests/unit/

# Интеграционные тесты
pytest tests/integration/

# Нагрузочное тестирование
python models/optimization/benchmark.py
```

## 📝 Основные компоненты

### Модель
- **Архитектура**: Fully Connected Neural Network
- **Фреймворк**: PyTorch / TensorFlow
- **Формат**: ONNX
- **Оптимизация**: Dynamic quantization (INT8)

### API
- **Фреймворк**: FastAPI
- **Валидация**: Pydantic
- **Документация**: автогенерируемая Swagger/ReDoc

### Infrastructure
- **IaC**: Terraform
- **Оркестрация**: Kubernetes
- **Storage**: S3-compatible Object Storage

### Мониторинг
- **Метрики**: Prometheus + Grafana
- **Логи**: ELK Stack / Loki
- **Дрифт**: Evidently AI

## 🔐 Безопасность

- Secrets хранятся в Kubernetes Secrets
- TLS/SSL для всех внешних соединений
- Network policies для изоляции
- Security scanning в CI/CD

## 🤝 Как сдавать проект

### Что должно быть в репозитории:

1. ✅ Все файлы из структуры выше
2. ✅ Рабочий README.md с инструкциями
3. ✅ requirements.txt с зависимостями
4. ✅ Документация в docs/ (опционально)
5. ✅ Скриншоты дашбордов в docs/screenshots/

### Что проверит преподаватель:

1. **Модель** - файлы в models/
2. **Terraform** - конфигурация в infrastructure/
3. **Docker** - Dockerfile и образ
4. **Kubernetes** - манифесты в deployment/
5. **CI/CD** - workflows в .github/workflows/
6. **Мониторинг** - конфигурация и скриншоты
7. **Документация** - README и комментарии в коде

### Рекомендации:

- Делайте коммиты по мере выполнения каждого этапа
- Добавьте скриншоты работающих сервисов
- Опишите проблемы, с которыми столкнулись
- Укажите, какие опциональные задачи выполнили

## 📚 Полезные ссылки

- [ONNX Documentation](https://onnx.ai/onnx/)
- [Terraform Yandex Cloud Provider](https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [Evidently AI](https://docs.evidentlyai.com/)
- [Prometheus](https://prometheus.io/docs/introduction/overview/)
- [Apache Airflow](https://airflow.apache.org/docs/)

## 📧 Контакты

Если есть вопросы по проекту, создайте Issue в репозитории.

## 📄 Лицензия

MIT License
