"""
FastAPI приложение для кредитного скоринга
Production-ready API с мониторингом и метриками
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import onnxruntime as ort
import numpy as np
import joblib
import logging
from datetime import datetime
import os

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time

# ============================================
# Конфигурация
# ============================================

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Пути к моделям
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../models/optimization/credit_scoring_quantized.onnx')
SCALER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../models/trained/scaler.pkl')

# ============================================
# Prometheus Metrics
# ============================================

# Счетчики запросов
request_count = Counter(
    'credit_scoring_requests_total',
    'Total number of prediction requests',
    ['status']
)

# Гистограмма времени обработки
request_duration = Histogram(
    'credit_scoring_request_duration_seconds',
    'Request duration in seconds',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Счетчик предсказаний по классам
prediction_counter = Counter(
    'credit_scoring_predictions_total',
    'Total predictions by class',
    ['prediction']
)

# Gauge для активных запросов
active_requests = Gauge(
    'credit_scoring_active_requests',
    'Number of active prediction requests'
)

# ============================================
# Pydantic Models
# ============================================

class CreditApplication(BaseModel):
    """Заявка на кредит"""
    
    age: int = Field(..., ge=18, le=100, description="Возраст заемщика")
    income: float = Field(..., gt=0, description="Годовой доход")
    loan_amount: float = Field(..., gt=0, description="Запрашиваемая сумма кредита")
    credit_history_length: int = Field(..., ge=0, le=50, description="Длительность кредитной истории (лет)")
    num_open_accounts: int = Field(..., ge=0, le=50, description="Количество открытых счетов")
    debt_to_income: float = Field(..., ge=0, le=1, description="Отношение долга к доходу")
    num_late_payments: int = Field(..., ge=0, le=100, description="Количество просроченных платежей")
    employment_length: int = Field(..., ge=0, le=50, description="Стаж работы (лет)")
    num_credit_inquiries: int = Field(..., ge=0, le=50, description="Количество кредитных запросов")
    credit_utilization: float = Field(..., ge=0, le=1, description="Процент использования кредита")
    
    @validator('debt_to_income', 'credit_utilization')
    def check_ratio(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Значение должно быть между 0 и 1')
        return v
    
    class Config:
        schema_extra = {
            "example": {
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
        }


class BatchCreditApplications(BaseModel):
    """Батч заявок на кредит"""
    applications: List[CreditApplication]


class PredictionResponse(BaseModel):
    """Ответ с предсказанием"""
    
    prediction: int = Field(..., description="0 - одобрено, 1 - отказано")
    probability: float = Field(..., description="Вероятность дефолта")
    risk_level: str = Field(..., description="Уровень риска: low, medium, high")
    timestamp: str = Field(..., description="Время предсказания")
    model_version: str = Field(..., description="Версия модели")


class BatchPredictionResponse(BaseModel):
    """Ответ с батч предсказаниями"""
    predictions: List[PredictionResponse]
    batch_size: int


class HealthResponse(BaseModel):
    """Статус здоровья сервиса"""
    status: str
    model_loaded: bool
    scaler_loaded: bool
    timestamp: str


# ============================================
# Model Loader
# ============================================

class ModelManager:
    """Менеджер для загрузки и управления моделями"""
    
    def __init__(self):
        self.session = None
        self.scaler = None
        self.model_version = "1.0.0"
        self.load_model()
    
    def load_model(self):
        """Загрузка ONNX модели и scaler"""
        try:
            # Загрузка ONNX модели
            logger.info(f"Loading ONNX model from: {MODEL_PATH}")
            self.session = ort.InferenceSession(MODEL_PATH)
            logger.info("✅ ONNX model loaded successfully")
            
            # Загрузка scaler
            logger.info(f"Loading scaler from: {SCALER_PATH}")
            self.scaler = joblib.load(SCALER_PATH)
            logger.info("✅ Scaler loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise
    
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Предобработка данных"""
        return self.scaler.transform(data).astype(np.float32)
    
    def predict(self, data: np.ndarray) -> np.ndarray:
        """Предсказание"""
        input_name = self.session.get_inputs()[0].name
        return self.session.run(None, {input_name: data})[0]
    
    def get_risk_level(self, probability: float) -> str:
        """Определение уровня риска"""
        if probability < 0.3:
            return "low"
        elif probability < 0.7:
            return "medium"
        else:
            return "high"


# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="Credit Scoring API",
    description="Production ML API for credit scoring with ONNX model",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация модели
model_manager = ModelManager()


# ============================================
# Middleware для метрик
# ============================================

@app.middleware("http")
async def track_requests(request, call_next):
    """Middleware для отслеживания метрик"""
    
    # Увеличиваем счетчик активных запросов
    active_requests.inc()
    
    # Засекаем время
    start_time = time.time()
    
    try:
        # Обрабатываем запрос
        response = await call_next(request)
        
        # Записываем метрики
        duration = time.time() - start_time
        request_duration.observe(duration)
        request_count.labels(status=response.status_code).inc()
        
        return response
    
    finally:
        # Уменьшаем счетчик активных запросов
        active_requests.dec()


# ============================================
# Endpoints
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """Корневой endpoint"""
    return {
        "message": "Credit Scoring API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Проверка здоровья сервиса"""
    return HealthResponse(
        status="healthy",
        model_loaded=model_manager.session is not None,
        scaler_loaded=model_manager.scaler is not None,
        timestamp=datetime.now().isoformat()
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus метрики"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_single(application: CreditApplication):
    """
    Предсказание для одной заявки
    
    Возвращает:
    - prediction: 0 (одобрено) или 1 (отказано)
    - probability: вероятность дефолта
    - risk_level: уровень риска
    """
    
    try:
        # Подготовка данных
        features = np.array([[
            application.age,
            application.income,
            application.loan_amount,
            application.credit_history_length,
            application.num_open_accounts,
            application.debt_to_income,
            application.num_late_payments,
            application.employment_length,
            application.num_credit_inquiries,
            application.credit_utilization
        ]])
        
        # Предобработка
        features_scaled = model_manager.preprocess(features)
        
        # Предсказание
        probability = model_manager.predict(features_scaled)[0][0]
        prediction = int(probability >= 0.5)
        risk_level = model_manager.get_risk_level(probability)
        
        # Обновление метрик
        prediction_counter.labels(prediction=str(prediction)).inc()
        
        logger.info(f"Prediction: {prediction}, Probability: {probability:.4f}")
        
        return PredictionResponse(
            prediction=prediction,
            probability=float(probability),
            risk_level=risk_level,
            timestamp=datetime.now().isoformat(),
            model_version=model_manager.model_version
        )
    
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
async def predict_batch(batch: BatchCreditApplications):
    """
    Батч предсказание для нескольких заявок
    
    Более эффективно для обработки множества заявок одновременно
    """
    
    try:
        # Подготовка данных
        features = []
        for app in batch.applications:
            features.append([
                app.age,
                app.income,
                app.loan_amount,
                app.credit_history_length,
                app.num_open_accounts,
                app.debt_to_income,
                app.num_late_payments,
                app.employment_length,
                app.num_credit_inquiries,
                app.credit_utilization
            ])
        
        features = np.array(features)
        
        # Предобработка
        features_scaled = model_manager.preprocess(features)
        
        # Предсказания
        probabilities = model_manager.predict(features_scaled)
        
        # Формирование ответов
        predictions = []
        for prob in probabilities:
            probability = float(prob[0])
            prediction = int(probability >= 0.5)
            risk_level = model_manager.get_risk_level(probability)
            
            # Обновление метрик
            prediction_counter.labels(prediction=str(prediction)).inc()
            
            predictions.append(PredictionResponse(
                prediction=prediction,
                probability=probability,
                risk_level=risk_level,
                timestamp=datetime.now().isoformat(),
                model_version=model_manager.model_version
            ))
        
        logger.info(f"Batch prediction completed for {len(predictions)} applications")
        
        return BatchPredictionResponse(
            predictions=predictions,
            batch_size=len(predictions)
        )
    
    except Exception as e:
        logger.error(f"Error during batch prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/info", tags=["Model"])
async def model_info():
    """Информация о модели"""
    return {
        "model_version": model_manager.model_version,
        "model_type": "ONNX Neural Network",
        "optimization": "INT8 Quantization",
        "input_features": 10,
        "output_classes": 2
    }


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения"""
    logger.info("🚀 Starting Credit Scoring API...")
    logger.info(f"Model version: {model_manager.model_version}")
    logger.info("✅ API is ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке приложения"""
    logger.info("Shutting down Credit Scoring API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
