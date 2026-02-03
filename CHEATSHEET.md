# 🚀 ШПАРГАЛКА - Команды для macOS Terminal

## 📥 После скачивания архива

```bash
# Распаковать архив
cd ~/Downloads  # или куда скачали
tar -xzf credit-scoring-mlops.tar.gz

# Перейти в проект
cd credit-scoring-mlops

# Посмотреть структуру
ls -la
```

---

## ⚡ БЫСТРЫЙ СТАРТ (30 минут)

```bash
# 1. Установка всех зависимостей
./setup.sh

# 2. Запуск полного пайплайна
./scripts/run_all.sh

# Готово! API запущен на http://localhost:8000
```

---

## 🎯 ПОШАГОВЫЙ ЗАПУСК

### Шаг 1: Установка
```bash
./setup.sh
```

### Шаг 2: Обучение модели
```bash
./scripts/train_model.sh
```

### Шаг 3: Конвертация в ONNX
```bash
./scripts/convert_onnx.sh
```

### Шаг 4: Оптимизация
```bash
./scripts/optimize_model.sh
```

### Шаг 5: Проверка дрифта
```bash
./scripts/check_drift.sh
```

### Шаг 6: Запуск API
```bash
./scripts/run_api.sh
```

### Шаг 7: Тестирование API (в новом окне Terminal)
```bash
cd ~/Downloads/credit-scoring-mlops
./scripts/test_api.sh
```

---

## 🌐 Открыть в браузере

```bash
# Swagger UI (документация API)
open http://localhost:8000/docs

# Проверка здоровья
open http://localhost:8000/health

# Метрики Prometheus
open http://localhost:8000/metrics
```

---

## 📊 Просмотр результатов

```bash
# Посмотреть размеры моделей
ls -lh models/trained/
ls -lh models/onnx/
ls -lh models/optimization/

# Открыть отчет о дрифте
open monitoring/evidently/reports/data_drift_report_*.html

# Посмотреть benchmark результаты
cat models/onnx/benchmark_results.json | python3 -m json.tool

# Посмотреть отчет оптимизации
cat models/optimization/optimization_report.json | python3 -m json.tool
```

---

## 📝 Логи

```bash
# Логи обучения
ls -lt logs/training_*.log | head -1 | awk '{print $9}' | xargs cat

# Логи API
tail -f logs/api_*.log

# Все логи
ls -lt logs/
```

---

## 🧪 Тестирование API через curl

```bash
# Health check
curl http://localhost:8000/health

# Информация о модели
curl http://localhost:8000/model/info

# Предсказание
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

## 🛑 Остановка API

```bash
# Найти процесс
lsof -i :8000

# Остановить
pkill -f uvicorn

# Или если знаете PID
kill <PID>
```

---

## 🧹 Очистка

```bash
# Удалить модели и логи (структура остается)
./scripts/clean.sh

# Полное удаление проекта
cd ..
rm -rf credit-scoring-mlops/
```

---

## 🔧 Решение проблем

### Если скрипт не запускается
```bash
chmod +x setup.sh
chmod +x scripts/*.sh
```

### Если нет Python 3.9+
```bash
brew install python@3.9
```

### Если нет Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Если порт 8000 занят
```bash
# Найти что использует порт
lsof -i :8000

# Остановить процесс
kill <PID>
```

### Активация окружения вручную
```bash
source venv/bin/activate
```

---

## 📸 Скриншоты для сдачи

```bash
# 1. Создать папку для скриншотов
mkdir -p docs/screenshots

# 2. Сделать скриншоты:
#    - Терминал с результатами обучения
#    - http://localhost:8000/docs (Swagger)
#    - Отчет о дрифте (HTML)
#    - Результаты тестов API
#    - Prometheus метрики

# 3. Переместить скриншоты
#    Просто drag & drop в docs/screenshots/
```

---

## 🎓 Подготовка к сдаче

```bash
# 1. Инициализация Git (если еще не сделано)
git init
git add .
git commit -m "Initial commit: Complete MLOps pipeline"

# 2. Создать репозиторий на GitHub

# 3. Загрузить код
git remote add origin https://github.com/YOUR_USERNAME/credit-scoring-mlops.git
git branch -M main
git push -u origin main

# 4. Добавить скриншоты
git add docs/screenshots/*
git commit -m "Add screenshots"
git push

# 5. Отправить ссылку преподавателю
```

---

## 📚 Документация

```bash
# Главная документация
cat README.md

# Быстрый старт
cat QUICKSTART.md

# Подробная инструкция
cat SETUP.md

# Архитектура
cat ARCHITECTURE.md

# Документация скриптов
cat scripts/README.md
```

---

## 💡 Полезные команды macOS

```bash
# Открыть папку в Finder
open .

# Открыть файл в текстовом редакторе
open -a TextEdit README.md

# Скопировать путь к файлу
pwd | pbcopy

# Посмотреть размер папки
du -sh .

# Найти файл
find . -name "*.py"

# Посмотреть процессы Python
ps aux | grep python
```

---

## 🆘 Если что-то не работает

```bash
# 1. Проверить версию Python
python3 --version

# 2. Проверить зависимости
pip list

# 3. Проверить виртуальное окружение
which python3

# 4. Посмотреть логи
ls -lt logs/ | head -5

# 5. Переустановить зависимости
./scripts/clean.sh
./setup.sh
```

---

## ⌨️ Горячие клавиши Terminal

- `Cmd + T` - Новая вкладка
- `Cmd + N` - Новое окно
- `Cmd + K` - Очистить экран
- `Ctrl + C` - Остановить процесс
- `Ctrl + Z` - Приостановить процесс
- `↑` / `↓` - История команд
- `Tab` - Автодополнение

---

**Сохраните эту шпаргалку!** 📌

Скопируйте в Notes.app или распечатайте для удобства.
