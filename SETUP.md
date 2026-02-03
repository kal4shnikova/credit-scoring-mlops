# 🚀 ПОШАГОВАЯ ИНСТРУКЦИЯ ПО ЗАПУСКУ ПРОЕКТА

Эта инструкция поможет вам шаг за шагом выполнить все этапы проекта.

## 📋 Предварительные требования

### Установите необходимое ПО:

1. **Python 3.9+**
```bash
python --version
```

2. **Docker & Docker Compose**
```bash
docker --version
docker-compose --version
```

3. **Git**
```bash
git --version
```

4. **Yandex Cloud CLI** (или CLI вашего облачного провайдера)
```bash
# Установка YC CLI
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# Инициализация
yc init
```

5. **Terraform**
```bash
# macOS
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

terraform --version
```

6. **kubectl**
```bash
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

kubectl version --client
```

---

## 🎯 ЭТАП 1: Подготовка модели

### 1.1 Клонирование репозитория

```bash
git clone https://github.com/your-username/credit-scoring-mlops.git
cd credit-scoring-mlops
```

### 1.2 Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows
```

### 1.3 Установка зависимостей

```bash
pip install -r requirements.txt
```

### 1.4 Обучение модели

```bash
cd models/training
python train_nn.py
```

**Ожидаемый результат:**
- Файл `models/trained/credit_scoring_nn.pth`
- Файл `models/trained/scaler.pkl`
- Логи обучения с метриками

### 1.5 Конвертация в ONNX

```bash
cd ../onnx
python convert_to_onnx.py
```

**Ожидаемый результат:**
- Файл `models/onnx/credit_scoring_model.onnx`
- Файл `models/onnx/benchmark_results.json`
- Сравнение производительности

### 1.6 Оптимизация (квантизация)

```bash
cd ../optimization
python quantize.py
```

**Ожидаемый результат:**
- Файл `models/optimization/credit_scoring_quantized.onnx`
- Файл `models/optimization/optimization_report.json`
- Метрики улучшения

**✅ Чеклист Этапа 1:**
- [ ] Модель обучена
- [ ] ONNX конвертация выполнена
- [ ] Оптимизация применена
- [ ] Бенчмарки проведены

---

## ☁️ ЭТАП 2: Cloud Infrastructure

### 2.1 Настройка Yandex Cloud

```bash
# Создайте каталог в Yandex Cloud через веб-интерфейс
# Получите OAuth token: https://oauth.yandex.ru/authorize?response_type=token&client_id=1a6990aa636648e9b2ef855fa7bec2fb

# Сохраните credentials
export YC_TOKEN="your_oauth_token"
export YC_CLOUD_ID="your_cloud_id"
export YC_FOLDER_ID="your_folder_id"
```

### 2.2 Создание S3 bucket для Terraform state

```bash
# Создайте Object Storage bucket через веб-интерфейс YC
# Или через CLI:
yc storage bucket create --name credit-scoring-terraform-state
```

### 2.3 Настройка Terraform

```bash
cd infrastructure/environments/production

# Копируйте пример файла с переменными
cp terraform.tfvars.example terraform.tfvars

# Отредактируйте terraform.tfvars с вашими значениями
nano terraform.tfvars
```

### 2.4 Инициализация Terraform

```bash
terraform init
```

### 2.5 Планирование инфраструктуры

```bash
terraform plan
```

Проверьте, что планируется создать корректная инфраструктура.

### 2.6 Применение конфигурации

```bash
terraform apply
```

⚠️ **ВНИМАНИЕ:** Это создаст реальные ресурсы в облаке, которые будут стоить денег!

**Ожидаемое время:** 10-15 минут

**Создастся:**
- VPC сеть
- Kubernetes кластер
- Node groups
- Object Storage buckets
- Мониторинг

### 2.7 Получение kubeconfig

```bash
yc managed-kubernetes cluster get-credentials <cluster-name> --external

# Проверка подключения
kubectl get nodes
```

**✅ Чеклист Этапа 2:**
- [ ] Terraform state bucket создан
- [ ] Инфраструктура развернута
- [ ] Kubernetes кластер доступен
- [ ] kubectl настроен

---

## 🐳 ЭТАП 3: Контейнеризация

### 3.1 Создание Docker образа

```bash
cd ../../../  # Возвращаемся в корень проекта

# Билд образа
docker build -t credit-scoring-api:latest -f deployment/docker/Dockerfile .
```

### 3.2 Тестирование локально

```bash
# Запуск контейнера
docker run -p 8000:8000 credit-scoring-api:latest

# В другом терминале проверьте
curl http://localhost:8000/health
```

### 3.3 Публикация в Container Registry

```bash
# GitHub Container Registry
docker login ghcr.io -u YOUR_GITHUB_USERNAME
docker tag credit-scoring-api:latest ghcr.io/YOUR_USERNAME/credit-scoring-api:latest
docker push ghcr.io/YOUR_USERNAME/credit-scoring-api:latest

# Или Yandex Container Registry
yc container registry create --name credit-scoring
docker tag credit-scoring-api:latest cr.yandex/<registry-id>/credit-scoring-api:latest
docker push cr.yandex/<registry-id>/credit-scoring-api:latest
```

**✅ Чеклист Этапа 3:**
- [ ] Docker образ собран
- [ ] Локальное тестирование пройдено
- [ ] Образ опубликован в registry

---

## ⚙️ ЭТАП 4: CI/CD Pipeline

### 4.1 Настройка GitHub Actions

1. Создайте репозиторий на GitHub
2. Push ваш код:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/credit-scoring-mlops.git
git push -u origin main
```

### 4.2 Настройка Secrets

В GitHub: Settings → Secrets and variables → Actions

Добавьте secrets:
- `KUBECONFIG` - base64 encoded kubeconfig для staging
- `KUBECONFIG_PROD` - base64 encoded kubeconfig для production
- `YC_TOKEN` - Yandex Cloud OAuth token

```bash
# Получить base64 kubeconfig
cat ~/.kube/config | base64
```

### 4.3 Создание окружений

GitHub: Settings → Environments

Создайте:
- `staging` (без ограничений)
- `production` (с required reviewers)

### 4.4 Тестирование CI/CD

```bash
# Создайте feature branch
git checkout -b feature/test-cicd

# Внесите изменения
echo "# Test" >> README.md
git add README.md
git commit -m "Test CI/CD"
git push origin feature/test-cicd

# Создайте Pull Request через веб-интерфейс
```

**✅ Чеклист Этапа 4:**
- [ ] GitHub репозиторий создан
- [ ] Secrets настроены
- [ ] Окружения созданы
- [ ] CI/CD pipeline протестирован

---

## 📊 ЭТАП 5: Мониторинг

### 5.1 Деплой Prometheus

```bash
# Используя Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/prometheus/values.yaml
```

### 5.2 Доступ к Grafana

```bash
# Port-forward для доступа
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Логин: admin
# Пароль:
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

Откройте: http://localhost:3000

### 5.3 Импорт дашбордов

1. В Grafana: Dashboards → Import
2. Загрузите JSON из `monitoring/grafana/dashboards/`

**✅ Чеклист Этапа 5:**
- [ ] Prometheus развернут
- [ ] Grafana доступна
- [ ] Дашборды импортированы
- [ ] Алерты настроены

---

## 🔍 ЭТАП 6: Мониторинг дрифта

### 6.1 Запуск мониторинга дрифта

```bash
cd monitoring/evidently
python drift_detection.py
```

### 6.2 Просмотр отчетов

```bash
# Откройте HTML отчеты в браузере
open reports/data_drift_report_*.html
open reports/target_drift_report_*.html
```

### 6.3 Настройка регулярного мониторинга

Добавьте в crontab:

```bash
crontab -e

# Добавьте строку (запуск каждый день в 2:00)
0 2 * * * cd /path/to/project && python monitoring/evidently/drift_detection.py
```

**✅ Чеклист Этапа 6:**
- [ ] Evidently установлен
- [ ] Отчеты о дрифте созданы
- [ ] Регулярный мониторинг настроен

---

## 🔄 ЭТАП 7: Автоматизация

### 7.1 Установка Apache Airflow

```bash
# Используя Docker Compose
cd airflow
docker-compose up -d

# Или в Kubernetes
helm repo add apache-airflow https://airflow.apache.org
helm install airflow apache-airflow/airflow --namespace airflow --create-namespace
```

### 7.2 Доступ к Airflow UI

```bash
# Port-forward
kubectl port-forward -n airflow svc/airflow-webserver 8080:8080

# Откройте: http://localhost:8080
# Логин: admin
# Пароль: admin
```

### 7.3 Деплой DAG

```bash
# Скопируйте DAG файлы
kubectl cp airflow/dags/ airflow/<airflow-pod>:/opt/airflow/dags/
```

### 7.4 Активация DAG

1. В Airflow UI найдите `credit_scoring_retraining`
2. Включите переключатель
3. Trigger DAG вручную для теста

**✅ Чеклист Этапа 7:**
- [ ] Airflow установлен
- [ ] DAG развернут
- [ ] Пайплайн протестирован

---

## 🎓 ЭТАП 8: Документация и сдача проекта

### 8.1 Создание скриншотов

Сделайте скриншоты:

1. **Grafana дашборд** - метрики API
2. **Prometheus alerts** - активные алерты
3. **Evidently отчеты** - дрифт анализ
4. **Airflow DAG** - успешный запуск
5. **Kubernetes pods** - `kubectl get pods`
6. **API endpoint** - Swagger UI

Сохраните в `docs/screenshots/`

### 8.2 Обновление README

```bash
# Обновите README.md с:
# - Актуальными ссылками
# - Результатами тестов
# - Полученными метриками
```

### 8.3 Финальный коммит

```bash
git add .
git commit -m "Complete MLOps pipeline implementation"
git push origin main
```

### 8.4 Подготовка к сдаче

**Создайте архив проекта:**

```bash
# Из корня проекта
tar -czf credit-scoring-mlops.tar.gz \
  --exclude=venv \
  --exclude=.git \
  --exclude=__pycache__ \
  --exclude=*.pyc \
  .
```

**Или просто отправьте ссылку на GitHub репозиторий**

---

## 📝 ЧТО СДАВАТЬ ПРЕПОДАВАТЕЛЮ

### Обязательно:

1. **GitHub репозиторий** с:
   - ✅ Всем кодом
   - ✅ README.md с инструкциями
   - ✅ Скриншотами в docs/screenshots/

2. **Документация:**
   - ✅ Описание архитектуры
   - ✅ Инструкции по запуску
   - ✅ Результаты тестов

3. **Доказательства работы:**
   - ✅ Скриншоты дашбордов
   - ✅ Логи успешных деплоев
   - ✅ Результаты бенчмарков

### Опционально (для дополнительных баллов):

- 🌟 Видео-демонстрация работы системы
- 🌟 Дополнительные метрики и визуализации
- 🌟 Расширенные функции (A/B тестирование, Blue-Green deployment)

---

## ❓ FAQ

### Q: Что делать, если нет доступа к облаку?

**A:** Используйте локальный Kubernetes:

```bash
# Установите Minikube
minikube start --cpus 4 --memory 8192

# Используйте локальный registry
minikube addons enable registry
```

### Q: Как сэкономить на облаке?

**A:** 
- Используйте preemptible nodes
- Останавливайте кластер когда не используете
- Используйте минимальные ресурсы
- Удаляйте инфраструктуру после демонстрации: `terraform destroy`

### Q: Ошибка при установке зависимостей

**A:** 
```bash
# Обновите pip
pip install --upgrade pip

# Установите с флагом --no-cache-dir
pip install --no-cache-dir -r requirements.txt
```

### Q: Как проверить что все работает?

**A:** 
```bash
# Запустите все тесты
pytest tests/

# Проверьте API
curl http://<API_URL>/health

# Проверьте метрики
curl http://<API_URL>/metrics
```

---

## 🆘 Поддержка

Если возникли проблемы:

1. Проверьте логи: `kubectl logs <pod-name>`
2. Проверьте статус: `kubectl describe pod <pod-name>`
3. Создайте Issue в репозитории проекта
4. Обратитесь к преподавателю

---

## 🎉 Удачи в выполнении проекта!

После завершения всех этапов у вас будет полноценная production-ready система машинного обучения с:

- ✅ Оптимизированной моделью
- ✅ Автоматизированным CI/CD
- ✅ Kubernetes оркестрацией
- ✅ Комплексным мониторингом
- ✅ Автоматическим переобучением

**Это серьезный проект для резюме!** 🚀
