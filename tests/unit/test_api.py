"""
Unit тесты для Credit Scoring API
"""

import pytest
from fastapi.testclient import TestClient
import sys
sys.path.append('../api')

from api.app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Тесты для health endpoint"""
    
    def test_health_check(self):
        """Проверка health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
        assert data["scaler_loaded"] is True
        assert "timestamp" in data
    
    def test_root_endpoint(self):
        """Проверка root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestPredictionEndpoint:
    """Тесты для prediction endpoint"""
    
    def test_valid_prediction(self):
        """Тест с валидными данными"""
        payload = {
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
        }
        
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "prediction" in data
        assert "probability" in data
        assert "risk_level" in data
        assert data["prediction"] in [0, 1]
        assert 0 <= data["probability"] <= 1
        assert data["risk_level"] in ["low", "medium", "high"]
    
    def test_invalid_age(self):
        """Тест с невалидным возрастом"""
        payload = {
            "age": 150,  # Невалидный возраст
            "income": 60000,
            "loan_amount": 15000,
            "credit_history_length": 10,
            "num_open_accounts": 5,
            "debt_to_income": 0.3,
            "num_late_payments": 0,
            "employment_length": 8,
            "num_credit_inquiries": 2,
            "credit_utilization": 0.4
        }
        
        response = client.post("/predict", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_missing_field(self):
        """Тест с отсутствующим полем"""
        payload = {
            "age": 35,
            "income": 60000,
            # Отсутствует loan_amount
            "credit_history_length": 10,
            "num_open_accounts": 5,
            "debt_to_income": 0.3,
            "num_late_payments": 0,
            "employment_length": 8,
            "num_credit_inquiries": 2,
            "credit_utilization": 0.4
        }
        
        response = client.post("/predict", json=payload)
        assert response.status_code == 422


class TestBatchPrediction:
    """Тесты для batch prediction endpoint"""
    
    def test_batch_prediction(self):
        """Тест batch предсказания"""
        payload = {
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
                    "age": 45,
                    "income": 80000,
                    "loan_amount": 25000,
                    "credit_history_length": 15,
                    "num_open_accounts": 8,
                    "debt_to_income": 0.5,
                    "num_late_payments": 2,
                    "employment_length": 12,
                    "num_credit_inquiries": 3,
                    "credit_utilization": 0.6
                }
            ]
        }
        
        response = client.post("/predict/batch", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "predictions" in data
        assert "batch_size" in data
        assert data["batch_size"] == 2
        assert len(data["predictions"]) == 2


class TestModelInfo:
    """Тесты для model info endpoint"""
    
    def test_model_info(self):
        """Проверка информации о модели"""
        response = client.get("/model/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "model_version" in data
        assert "model_type" in data
        assert "optimization" in data


class TestMetrics:
    """Тесты для metrics endpoint"""
    
    def test_prometheus_metrics(self):
        """Проверка Prometheus метрик"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "credit_scoring" in response.text


# Fixtures для тестов

@pytest.fixture
def valid_application():
    """Fixture с валидной заявкой"""
    return {
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
    }


@pytest.fixture
def risky_application():
    """Fixture с рискованной заявкой"""
    return {
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
    }


def test_with_fixtures(valid_application, risky_application):
    """Тест с использованием fixtures"""
    
    # Valid application
    response = client.post("/predict", json=valid_application)
    assert response.status_code == 200
    valid_result = response.json()
    
    # Risky application
    response = client.post("/predict", json=risky_application)
    assert response.status_code == 200
    risky_result = response.json()
    
    # Рискованная заявка должна иметь более высокую вероятность дефолта
    assert risky_result["probability"] >= valid_result["probability"]
