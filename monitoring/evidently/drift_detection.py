"""
Мониторинг дрифта модели с Evidently AI
Этап 6: Мониторинг дрифта и управление моделями
"""

from evidently.report import Report
from evidently.metrics import (
    DataDriftTable,
    DatasetDriftMetric,
    ColumnDriftMetric,
)
from evidently.metric_preset import (
    DataDriftPreset,
    DataQualityPreset,
    TargetDriftPreset,
)
from evidently.test_suite import TestSuite
from evidently.tests import (
    TestNumberOfDriftedColumns,
    TestShareOfDriftedColumns,
    TestAccuracyScore,
)

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание директорий
Path("../../monitoring/evidently/reports").mkdir(parents=True, exist_ok=True)


class DriftMonitor:
    """Класс для мониторинга дрифта данных и модели"""
    
    def __init__(self, reference_data_path, current_data_path=None):
        """
        Args:
            reference_data_path: путь к эталонным данным (train data)
            current_data_path: путь к текущим данным (production data)
        """
        self.reference_data_path = reference_data_path
        self.current_data_path = current_data_path
        
        # Загрузка данных
        self.reference_data = self._load_data(reference_data_path)
        
        if current_data_path:
            self.current_data = self._load_data(current_data_path)
        else:
            # Создаем синтетические текущие данные для демонстрации
            self.current_data = self._generate_current_data()
    
    def _load_data(self, path):
        """Загрузка данных"""
        if Path(path).exists():
            return pd.read_csv(path)
        else:
            logger.warning(f"File not found: {path}")
            return None
    
    def _generate_current_data(self):
        """Генерация синтетических текущих данных с дрифтом"""
        logger.info("Generating synthetic current data with drift...")
        
        np.random.seed(123)
        n_samples = 1000
        
        # Создаем данные с небольшим дрифтом
        df = pd.DataFrame({
            'age': np.random.randint(20, 75, n_samples),  # Немного другое распределение
            'income': np.random.lognormal(10.7, 0.9, n_samples),  # Drift: выше доход
            'loan_amount': np.random.lognormal(9.2, 1.1, n_samples),  # Drift: больше суммы
            'credit_history_length': np.random.randint(0, 35, n_samples),
            'num_open_accounts': np.random.randint(0, 18, n_samples),
            'debt_to_income': np.random.uniform(0, 0.9, n_samples),  # Drift: выше долг
            'num_late_payments': np.random.poisson(1.5, n_samples),  # Drift: больше просрочек
            'employment_length': np.random.randint(0, 42, n_samples),
            'num_credit_inquiries': np.random.poisson(2.5, n_samples),
            'credit_utilization': np.random.uniform(0, 0.95, n_samples),
        })
        
        # Целевая переменная (с concept drift)
        default_prob = (
            -0.025 * df['age'] +  # Drift: коэффициент изменился
            -0.00001 * df['income'] +
            0.00003 * df['loan_amount'] +  # Drift: влияние усилилось
            -0.01 * df['credit_history_length'] +
            0.04 * df['num_late_payments'] +  # Drift: влияние усилилось
            0.6 * df['debt_to_income'] +
            0.12 * df['credit_utilization'] +
            np.random.normal(0, 0.1, n_samples)
        )
        df['default'] = (1 / (1 + np.exp(-default_prob)) > 0.5).astype(int)
        
        return df
    
    def generate_data_drift_report(self):
        """Генерация отчета о дрифте данных"""
        logger.info("Generating data drift report...")
        
        # Создание отчета
        report = Report(metrics=[
            DataDriftPreset(),
            DataQualityPreset(),
        ])
        
        # Запуск отчета
        report.run(
            reference_data=self.reference_data,
            current_data=self.current_data
        )
        
        # Сохранение HTML отчета
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = f"../../monitoring/evidently/reports/data_drift_report_{timestamp}.html"
        report.save_html(html_path)
        
        logger.info(f"Data drift report saved: {html_path}")
        
        # Извлечение метрик
        report_dict = report.as_dict()
        
        return report, html_path
    
    def generate_target_drift_report(self):
        """Генерация отчета о дрифте целевой переменной"""
        logger.info("Generating target drift report...")
        
        report = Report(metrics=[
            TargetDriftPreset(),
        ])
        
        report.run(
            reference_data=self.reference_data,
            current_data=self.current_data
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = f"../../monitoring/evidently/reports/target_drift_report_{timestamp}.html"
        report.save_html(html_path)
        
        logger.info(f"Target drift report saved: {html_path}")
        
        return report, html_path
    
    def generate_column_drift_report(self, column_name):
        """Детальный отчет о дрифте конкретного признака"""
        logger.info(f"Generating column drift report for: {column_name}")
        
        report = Report(metrics=[
            ColumnDriftMetric(column_name=column_name),
        ])
        
        report.run(
            reference_data=self.reference_data,
            current_data=self.current_data
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = f"../../monitoring/evidently/reports/column_drift_{column_name}_{timestamp}.html"
        report.save_html(html_path)
        
        logger.info(f"Column drift report saved: {html_path}")
        
        return report, html_path
    
    def run_drift_tests(self):
        """Запуск тестов на дрифт"""
        logger.info("Running drift tests...")
        
        # Создание test suite
        test_suite = TestSuite(tests=[
            TestNumberOfDriftedColumns(),
            TestShareOfDriftedColumns(lt=0.3),  # Меньше 30% колонок с дрифтом
        ])
        
        # Запуск тестов
        test_suite.run(
            reference_data=self.reference_data,
            current_data=self.current_data
        )
        
        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = f"../../monitoring/evidently/reports/drift_tests_{timestamp}.html"
        test_suite.save_html(html_path)
        
        # Получение результатов
        results = test_suite.as_dict()
        
        # Проверка на пройденные тесты
        all_passed = all(
            test['status'] == 'SUCCESS'
            for test in results['tests']
        )
        
        if all_passed:
            logger.info("✅ All drift tests passed!")
        else:
            logger.warning("⚠️  Some drift tests failed!")
            for test in results['tests']:
                if test['status'] != 'SUCCESS':
                    logger.warning(f"  - {test['name']}: {test['status']}")
        
        logger.info(f"Drift tests report saved: {html_path}")
        
        return test_suite, all_passed, html_path
    
    def get_drift_metrics(self):
        """Получение численных метрик дрифта для Prometheus"""
        logger.info("Calculating drift metrics...")
        
        # Создаем отчет для извлечения метрик
        report = Report(metrics=[
            DatasetDriftMetric(),
        ])
        
        report.run(
            reference_data=self.reference_data,
            current_data=self.current_data
        )
        
        # Извлекаем метрики
        report_dict = report.as_dict()
        
        # Получаем метрики дрифта
        drift_metrics = {}
        
        for metric in report_dict['metrics']:
            if metric['metric'] == 'DatasetDriftMetric':
                result = metric['result']
                drift_metrics['dataset_drift_score'] = result.get('drift_share', 0)
                drift_metrics['number_of_drifted_columns'] = result.get('number_of_drifted_columns', 0)
                drift_metrics['number_of_columns'] = result.get('number_of_columns', 0)
        
        # Сохраняем метрики в JSON для Prometheus
        metrics_path = "../../monitoring/evidently/metrics/drift_metrics.json"
        Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(metrics_path, 'w') as f:
            json.dump(drift_metrics, f, indent=2)
        
        logger.info(f"Drift metrics saved: {metrics_path}")
        logger.info(f"Drift metrics: {drift_metrics}")
        
        return drift_metrics
    
    def should_retrain(self, drift_threshold=0.3):
        """
        Определение необходимости переобучения модели
        
        Args:
            drift_threshold: порог дрифта (доля колонок с дрифтом)
        
        Returns:
            bool: нужно ли переобучать модель
        """
        metrics = self.get_drift_metrics()
        
        drift_share = metrics.get('dataset_drift_score', 0)
        
        should_retrain = drift_share > drift_threshold
        
        if should_retrain:
            logger.warning(f"⚠️  Drift detected: {drift_share:.2%} > {drift_threshold:.2%}")
            logger.warning("Model retraining recommended!")
        else:
            logger.info(f"✅ Drift level acceptable: {drift_share:.2%} <= {drift_threshold:.2%}")
        
        return should_retrain


def main():
    """Основная функция мониторинга"""
    
    print("=" * 60)
    print("МОНИТОРИНГ ДРИФТА С EVIDENTLY AI")
    print("=" * 60)
    
    # Пути к данным
    REFERENCE_DATA = '../../data/processed/train.csv'
    CURRENT_DATA = None  # Будут созданы синтетические данные
    
    # Инициализация монитора
    monitor = DriftMonitor(REFERENCE_DATA, CURRENT_DATA)
    
    # 1. Отчет о дрифте данных
    print("\n📊 Генерация отчета о дрифте данных...")
    data_drift_report, data_drift_path = monitor.generate_data_drift_report()
    print(f"✅ Отчет сохранен: {data_drift_path}")
    
    # 2. Отчет о дрифте целевой переменной
    print("\n🎯 Генерация отчета о дрифте целевой переменной...")
    target_drift_report, target_drift_path = monitor.generate_target_drift_report()
    print(f"✅ Отчет сохранен: {target_drift_path}")
    
    # 3. Детальные отчеты по критичным признакам
    print("\n🔍 Генерация детальных отчетов...")
    critical_features = ['income', 'loan_amount', 'debt_to_income']
    
    for feature in critical_features:
        _, feature_report_path = monitor.generate_column_drift_report(feature)
        print(f"✅ Отчет для {feature}: {feature_report_path}")
    
    # 4. Тесты на дрифт
    print("\n🧪 Запуск тестов на дрифт...")
    test_suite, all_passed, tests_path = monitor.run_drift_tests()
    print(f"✅ Результаты тестов: {tests_path}")
    
    # 5. Метрики для Prometheus
    print("\n📈 Расчет метрик для Prometheus...")
    drift_metrics = monitor.get_drift_metrics()
    
    # 6. Проверка необходимости переобучения
    print("\n🤖 Проверка необходимости переобучения...")
    should_retrain = monitor.should_retrain(drift_threshold=0.3)
    
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    print(f"\n📊 Метрики дрифта:")
    print(f"  - Доля колонок с дрифтом: {drift_metrics.get('dataset_drift_score', 0):.2%}")
    print(f"  - Количество колонок с дрифтом: {drift_metrics.get('number_of_drifted_columns', 0)}")
    print(f"\n🧪 Тесты: {'✅ Пройдены' if all_passed else '❌ Провалены'}")
    print(f"\n🤖 Переобучение: {'⚠️  Рекомендуется' if should_retrain else '✅ Не требуется'}")
    
    print("\n📁 Все отчеты сохранены в: monitoring/evidently/reports/")
    print("💡 Откройте HTML файлы в браузере для просмотра")
    
    return monitor


if __name__ == "__main__":
    monitor = main()
