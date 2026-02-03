# 🚀 QUICK START - Минимальный набор действий

## За 30 минут до первого результата

### 1. Установка зависимостей (5 мин)

```bash
cd credit-scoring-mlops
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install torch scikit-learn onnx onnxruntime joblib numpy pandas
```

### 2. Обучение модели (10 мин)

```bash
cd models/training
python train_nn.py
```

**Результат:** Модель обучена → `models/trained/credit_scoring_nn.pth`

### 3. Конвертация в ONNX (5 мин)

```bash
cd ../onnx
python convert_to_onnx.py
```

**Результат:** ONNX модель → `models/onnx/credit_scoring_model.onnx`

### 4. Оптимизация (5 мин)

```bash
cd ../optimization
python quantize.py
```

**Результат:** Оптимизированная модель → `models/optimization/credit_scoring_quantized.onnx`

### 5. Локальный запуск API (5 мин)

```bash
cd ../../api
pip install fastapi uvicorn pydantic prometheus-client
uvicorn app.main:app --reload
```

**Результат:** API доступен на http://localhost:8000

### Проверка работы

```bash
# Health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs

# Тестовый запрос
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

---

## 🎯 ЧТО СДАВАТЬ (минимум для зачета)

### Обязательные файлы:

✅ **Этап 1 - Модель:**
- `models/trained/credit_scoring_nn.pth`
- `models/onnx/credit_scoring_model.onnx`
- `models/optimization/credit_scoring_quantized.onnx`
- `models/optimization/optimization_report.json`

✅ **Этап 2 - Infrastructure:**
- `infrastructure/` (вся папка с Terraform)
- Скриншот созданного Kubernetes кластера

✅ **Этап 3 - Docker:**
- `deployment/docker/Dockerfile`
- Скриншот запущенного контейнера

✅ **Этап 4 - CI/CD:**
- `.github/workflows/ci-cd.yml`
- Скриншот успешного GitHub Actions run

✅ **Этап 5 - Monitoring:**
- `monitoring/prometheus/prometheus.yml`
- `monitoring/prometheus/rules/alerts.yml`
- Скриншот Grafana dashboard

✅ **Этап 6 - Drift:**
- `monitoring/evidently/drift_detection.py`
- HTML отчет о дрифте

✅ **Этап 7 - Automation:**
- `airflow/dags/retraining_dag.py`

✅ **Документация:**
- `README.md` (главный)
- `SETUP.md` (инструкции)

---

## 📸 Обязательные скриншоты

1. **Консоль с результатами обучения** - метрики модели
2. **ONNX benchmark** - сравнение производительности
3. **Grafana dashboard** - метрики API
4. **Kubernetes pods** - `kubectl get pods -A`
5. **Evidently report** - HTML отчет
6. **Swagger UI** - документация API

Сохраните все в `docs/screenshots/`

---

## 💡 Лайфхаки

### Если нет облака:
Используйте Minikube для локального Kubernetes:
```bash
minikube start
kubectl get nodes
```

### Если мало времени:
Сосредоточьтесь на этапах 1-3 (модель + Docker), это основа.

### Если есть ошибки:
1. Проверьте версии Python (нужен 3.9+)
2. Установите зависимости по одной: `pip install <package>`
3. Читайте логи: они почти всегда говорят, в чем проблема

---

## 🆘 Помощь

**Telegram канал:** [если есть]
**Email:** [если есть]
**Issues:** https://github.com/your-repo/issues

---

## ✅ Финальный чеклист

- [ ] Модель обучена и работает
- [ ] ONNX конвертация выполнена
- [ ] Docker образ собран
- [ ] Terraform конфигурация создана
- [ ] CI/CD пайплайн настроен
- [ ] README.md заполнен
- [ ] Скриншоты сделаны
- [ ] GitHub репозиторий создан
- [ ] Все файлы залиты в git
- [ ] Ссылка отправлена преподавателю

**После выполнения всех пунктов - проект готов к сдаче! 🎉**
