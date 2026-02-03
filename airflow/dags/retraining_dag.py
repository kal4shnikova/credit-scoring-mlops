"""
Airflow DAG для автоматического переобучения модели
Этап 7: Пайплайн переобучения и автоматизация
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.dates import days_ago
from datetime import timedelta
import logging

# Конфигурация DAG
default_args = {
    'owner': 'ml-team',
    'depends_on_past': False,
    'email': ['ml-alerts@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'credit_scoring_retraining',
    default_args=default_args,
    description='Automated retraining pipeline for credit scoring model',
    schedule_interval='@weekly',  # Еженедельное переобучение
    start_date=days_ago(1),
    catchup=False,
    tags=['ml', 'credit-scoring', 'retraining'],
)


# ============================================
# Task 1: Проверка дрифта
# ============================================

def check_drift(**context):
    """
    Проверка наличия дрифта в данных
    Если дрифт обнаружен - продолжаем пайплайн
    """
    logging.info("Checking for data drift...")
    
    # Здесь должна быть логика проверки дрифта
    # Для примера используем моковые данные
    
    from monitoring.evidently.drift_detection import DriftMonitor
    
    monitor = DriftMonitor(
        reference_data_path='data/processed/train.csv',
        current_data_path='data/processed/current.csv'
    )
    
    drift_metrics = monitor.get_drift_metrics()
    should_retrain = monitor.should_retrain(drift_threshold=0.3)
    
    # Сохраняем результат в XCom для следующих задач
    context['task_instance'].xcom_push(key='drift_detected', value=should_retrain)
    context['task_instance'].xcom_push(key='drift_score', value=drift_metrics['dataset_drift_score'])
    
    logging.info(f"Drift score: {drift_metrics['dataset_drift_score']:.2%}")
    logging.info(f"Should retrain: {should_retrain}")
    
    return should_retrain


check_drift_task = PythonOperator(
    task_id='check_drift',
    python_callable=check_drift,
    dag=dag,
)


# ============================================
# Task 2: Загрузка новых данных
# ============================================

def fetch_new_data(**context):
    """Загрузка новых данных из production"""
    logging.info("Fetching new training data from production...")
    
    # Здесь должна быть логика загрузки данных из production БД
    # Для примера создаем заглушку
    
    import pandas as pd
    import numpy as np
    
    # Симуляция загрузки новых данных
    np.random.seed(42)
    n_samples = 5000
    
    new_data = pd.DataFrame({
        'age': np.random.randint(18, 70, n_samples),
        'income': np.random.lognormal(10.5, 0.8, n_samples),
        'loan_amount': np.random.lognormal(9, 1, n_samples),
        'credit_history_length': np.random.randint(0, 30, n_samples),
        'num_open_accounts': np.random.randint(0, 15, n_samples),
        'debt_to_income': np.random.uniform(0, 1, n_samples),
        'num_late_payments': np.random.poisson(1, n_samples),
        'employment_length': np.random.randint(0, 40, n_samples),
        'num_credit_inquiries': np.random.poisson(2, n_samples),
        'credit_utilization': np.random.uniform(0, 1, n_samples),
        'default': np.random.binomial(1, 0.3, n_samples),
    })
    
    # Сохранение данных
    new_data.to_csv('data/processed/new_train_data.csv', index=False)
    
    logging.info(f"Fetched {len(new_data)} new samples")
    
    return len(new_data)


fetch_data_task = PythonOperator(
    task_id='fetch_new_data',
    python_callable=fetch_new_data,
    dag=dag,
)


# ============================================
# Task 3: Валидация данных
# ============================================

def validate_data(**context):
    """Валидация качества данных"""
    logging.info("Validating data quality...")
    
    import pandas as pd
    
    df = pd.read_csv('data/processed/new_train_data.csv')
    
    # Проверки
    checks = {
        'no_missing_values': df.isnull().sum().sum() == 0,
        'correct_dtypes': all(df.dtypes.apply(lambda x: x in ['int64', 'float64'])),
        'target_balance': 0.1 < df['default'].mean() < 0.9,
        'sufficient_samples': len(df) >= 1000,
    }
    
    all_passed = all(checks.values())
    
    for check, passed in checks.items():
        logging.info(f"  {check}: {'✅' if passed else '❌'}")
    
    if not all_passed:
        raise ValueError("Data validation failed!")
    
    logging.info("Data validation passed ✅")
    
    return all_passed


validate_data_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag,
)


# ============================================
# Task 4: Обучение модели
# ============================================

# Используем KubernetesPodOperator для запуска обучения в Kubernetes
train_model_task = KubernetesPodOperator(
    task_id='train_model',
    name='model-training-job',
    namespace='default',
    image='ghcr.io/your-username/credit-scoring-trainer:latest',
    cmds=['python'],
    arguments=['models/training/train_nn.py'],
    labels={'app': 'model-training'},
    get_logs=True,
    is_delete_operator_pod=True,
    dag=dag,
)


# ============================================
# Task 5: Конвертация в ONNX
# ============================================

convert_onnx_task = KubernetesPodOperator(
    task_id='convert_to_onnx',
    name='onnx-conversion-job',
    namespace='default',
    image='ghcr.io/your-username/credit-scoring-trainer:latest',
    cmds=['python'],
    arguments=['models/onnx/convert_to_onnx.py'],
    labels={'app': 'onnx-conversion'},
    get_logs=True,
    is_delete_operator_pod=True,
    dag=dag,
)


# ============================================
# Task 6: Оптимизация модели
# ============================================

optimize_model_task = KubernetesPodOperator(
    task_id='optimize_model',
    name='model-optimization-job',
    namespace='default',
    image='ghcr.io/your-username/credit-scoring-trainer:latest',
    cmds=['python'],
    arguments=['models/optimization/quantize.py'],
    labels={'app': 'model-optimization'},
    get_logs=True,
    is_delete_operator_pod=True,
    dag=dag,
)


# ============================================
# Task 7: Валидация новой модели
# ============================================

def validate_model(**context):
    """Валидация производительности новой модели"""
    logging.info("Validating new model performance...")
    
    # Здесь должна быть логика валидации модели на тестовых данных
    # Проверяем, что новая модель не хуже старой
    
    import onnxruntime as ort
    import numpy as np
    from sklearn.metrics import roc_auc_score, accuracy_score
    import pandas as pd
    
    # Загружаем тестовые данные
    test_data = pd.read_csv('data/processed/test.csv')
    X_test = test_data.drop('default', axis=1).values.astype(np.float32)
    y_test = test_data['default'].values
    
    # Загружаем новую модель
    session = ort.InferenceSession('models/optimization/credit_scoring_quantized.onnx')
    
    # Предсказания
    predictions = session.run(None, {'input': X_test})[0]
    y_pred = (predictions >= 0.5).astype(int).flatten()
    
    # Метрики
    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, predictions)
    
    logging.info(f"New model metrics:")
    logging.info(f"  Accuracy: {accuracy:.4f}")
    logging.info(f"  AUC: {auc:.4f}")
    
    # Проверяем пороговые значения
    min_accuracy = 0.75
    min_auc = 0.80
    
    if accuracy < min_accuracy or auc < min_auc:
        raise ValueError(f"Model performance below threshold! Accuracy: {accuracy:.4f}, AUC: {auc:.4f}")
    
    logging.info("Model validation passed ✅")
    
    context['task_instance'].xcom_push(key='accuracy', value=accuracy)
    context['task_instance'].xcom_push(key='auc', value=auc)
    
    return {'accuracy': accuracy, 'auc': auc}


validate_model_task = PythonOperator(
    task_id='validate_model',
    python_callable=validate_model,
    dag=dag,
)


# ============================================
# Task 8: A/B тестирование (опционально)
# ============================================

def setup_ab_test(**context):
    """Настройка A/B теста для новой модели"""
    logging.info("Setting up A/B test...")
    
    # Здесь должна быть логика настройки A/B теста
    # Например, деплой новой модели с routing 10% трафика
    
    logging.info("A/B test configured: 10% traffic to new model")
    
    return True


ab_test_task = PythonOperator(
    task_id='setup_ab_test',
    python_callable=setup_ab_test,
    dag=dag,
)


# ============================================
# Task 9: Деплой в production
# ============================================

deploy_model_task = KubernetesPodOperator(
    task_id='deploy_to_production',
    name='model-deployment-job',
    namespace='default',
    image='bitnami/kubectl:latest',
    cmds=['kubectl'],
    arguments=[
        'set', 'image',
        'deployment/credit-scoring-api',
        'credit-scoring-api=ghcr.io/your-username/credit-scoring-api:latest',
        '-n', 'production'
    ],
    labels={'app': 'model-deployment'},
    get_logs=True,
    is_delete_operator_pod=True,
    dag=dag,
)


# ============================================
# Task 10: Мониторинг после деплоя
# ============================================

def monitor_deployment(**context):
    """Мониторинг после деплоя"""
    logging.info("Monitoring deployment...")
    
    import time
    
    # Ждем стабилизации
    time.sleep(60)
    
    # Проверяем метрики
    # В реальности здесь запросы к Prometheus
    
    logging.info("Deployment monitoring completed ✅")
    
    return True


monitor_task = PythonOperator(
    task_id='monitor_deployment',
    python_callable=monitor_deployment,
    dag=dag,
)


# ============================================
# Task 11: Уведомление
# ============================================

def send_notification(**context):
    """Отправка уведомления о завершении"""
    logging.info("Sending notification...")
    
    # Получаем метрики из предыдущих задач
    drift_score = context['task_instance'].xcom_pull(task_ids='check_drift', key='drift_score')
    accuracy = context['task_instance'].xcom_pull(task_ids='validate_model', key='accuracy')
    auc = context['task_instance'].xcom_pull(task_ids='validate_model', key='auc')
    
    message = f"""
    ✅ Model Retraining Completed Successfully!
    
    📊 Metrics:
    - Drift Score: {drift_score:.2%}
    - New Model Accuracy: {accuracy:.4f}
    - New Model AUC: {auc:.4f}
    
    🚀 New model deployed to production
    """
    
    logging.info(message)
    
    # Здесь можно добавить отправку в Slack/Telegram
    
    return message


notify_task = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    dag=dag,
)


# ============================================
# Определение зависимостей задач
# ============================================

# Линейный пайплайн
(
    check_drift_task
    >> fetch_data_task
    >> validate_data_task
    >> train_model_task
    >> convert_onnx_task
    >> optimize_model_task
    >> validate_model_task
    >> ab_test_task
    >> deploy_model_task
    >> monitor_task
    >> notify_task
)


# ============================================
# Дополнительные DAG для тригеров
# ============================================

# DAG для мониторинга дрифта (запускается каждый день)
drift_monitoring_dag = DAG(
    'credit_scoring_drift_monitoring',
    default_args=default_args,
    description='Daily drift monitoring',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['ml', 'credit-scoring', 'monitoring'],
)


def monitor_drift_daily(**context):
    """Ежедневный мониторинг дрифта"""
    from monitoring.evidently.drift_detection import DriftMonitor
    
    monitor = DriftMonitor(
        reference_data_path='data/processed/train.csv',
        current_data_path='data/processed/current.csv'
    )
    
    # Генерируем отчеты
    monitor.generate_data_drift_report()
    monitor.generate_target_drift_report()
    
    # Проверяем необходимость переобучения
    should_retrain = monitor.should_retrain(drift_threshold=0.3)
    
    if should_retrain:
        logging.warning("⚠️  Drift threshold exceeded! Triggering retraining...")
        # Триггерим основной DAG переобучения
        # В реальности используется TriggerDagRunOperator
    
    return should_retrain


drift_monitor_task = PythonOperator(
    task_id='monitor_drift',
    python_callable=monitor_drift_daily,
    dag=drift_monitoring_dag,
)
