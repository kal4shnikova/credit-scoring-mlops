"""
Оптимизация ONNX модели через квантизацию (quantization)
Этап 1: Подготовка модели к промышленной эксплуатации
"""

import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
import numpy as np
import time
import json
from pathlib import Path

Path("../../models/optimization").mkdir(parents=True, exist_ok=True)


def quantize_onnx_model(input_model_path, output_model_path):
    """
    Динамическая квантизация ONNX модели
    Преобразует веса из FP32 в INT8 для уменьшения размера и ускорения
    """
    
    print("🔧 Начинаем квантизацию модели...")
    print(f"  Входная модель: {input_model_path}")
    print(f"  Выходная модель: {output_model_path}")
    
    # Динамическая квантизация
    quantize_dynamic(
        input_model_path,
        output_model_path,
        weight_type=QuantType.QInt8  # Квантизация весов в INT8
    )
    
    print("✅ Квантизация завершена!")
    
    return output_model_path


def compare_model_sizes(original_path, quantized_path):
    """Сравнение размеров моделей"""
    
    import os
    
    original_size = os.path.getsize(original_path) / (1024 * 1024)  # MB
    quantized_size = os.path.getsize(quantized_path) / (1024 * 1024)  # MB
    
    reduction = ((original_size - quantized_size) / original_size) * 100
    
    print("\n📦 Сравнение размеров:")
    print(f"  Оригинальная модель: {original_size:.2f} MB")
    print(f"  Квантизованная модель: {quantized_size:.2f} MB")
    print(f"  Уменьшение: {reduction:.1f}%")
    
    return {
        'original_size_mb': original_size,
        'quantized_size_mb': quantized_size,
        'reduction_percent': reduction
    }


def benchmark_inference(model_path, model_name, n_samples=100, n_runs=1000):
    """
    Бенчмарк производительности инференса
    
    Args:
        model_path: путь к ONNX модели
        model_name: название модели для отчета
        n_samples: количество образцов для теста
        n_runs: количество итераций
    """
    
    print(f"\n⚡ Бенчмарк: {model_name}")
    
    # Создание сессии ONNX Runtime
    session = ort.InferenceSession(model_path)
    
    # Получение информации о входе
    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape
    
    # Генерация тестовых данных
    # Предполагаем, что первое измерение - batch size
    test_input = np.random.randn(n_samples, input_shape[1]).astype(np.float32)
    
    # Прогрев (warm-up)
    for _ in range(10):
        _ = session.run(None, {input_name: test_input})
    
    # Бенчмарк
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        _ = session.run(None, {input_name: test_input})
        times.append(time.perf_counter() - start)
    
    # Статистика
    times = np.array(times) * 1000  # конвертируем в миллисекунды
    
    results = {
        'mean_ms': float(np.mean(times)),
        'std_ms': float(np.std(times)),
        'min_ms': float(np.min(times)),
        'max_ms': float(np.max(times)),
        'median_ms': float(np.median(times)),
        'p95_ms': float(np.percentile(times, 95)),
        'p99_ms': float(np.percentile(times, 99)),
        'throughput_samples_per_sec': float(n_samples / (np.mean(times) / 1000))
    }
    
    print(f"  Среднее время: {results['mean_ms']:.4f} ± {results['std_ms']:.4f} ms")
    print(f"  Медиана: {results['median_ms']:.4f} ms")
    print(f"  P95: {results['p95_ms']:.4f} ms")
    print(f"  P99: {results['p99_ms']:.4f} ms")
    print(f"  Пропускная способность: {results['throughput_samples_per_sec']:.0f} samples/sec")
    
    return results


def validate_accuracy(original_model_path, quantized_model_path, n_samples=1000):
    """
    Проверка точности квантизованной модели
    Сравнение с оригинальной моделью
    """
    
    print("\n🎯 Проверка точности квантизованной модели...")
    
    # Создание сессий
    original_session = ort.InferenceSession(original_model_path)
    quantized_session = ort.InferenceSession(quantized_model_path)
    
    # Генерация тестовых данных
    input_name = original_session.get_inputs()[0].name
    input_shape = original_session.get_inputs()[0].shape
    test_input = np.random.randn(n_samples, input_shape[1]).astype(np.float32)
    
    # Инференс
    original_output = original_session.run(None, {input_name: test_input})[0]
    quantized_output = quantized_session.run(None, {input_name: test_input})[0]
    
    # Метрики различия
    mae = np.mean(np.abs(original_output - quantized_output))
    mse = np.mean((original_output - quantized_output) ** 2)
    max_diff = np.max(np.abs(original_output - quantized_output))
    
    # Корреляция
    correlation = np.corrcoef(
        original_output.flatten(),
        quantized_output.flatten()
    )[0, 1]
    
    print(f"  MAE (Mean Absolute Error): {mae:.6f}")
    print(f"  MSE (Mean Squared Error): {mse:.6f}")
    print(f"  Max Difference: {max_diff:.6f}")
    print(f"  Correlation: {correlation:.6f}")
    
    if correlation > 0.99:
        print("✅ Точность сохранена! Корреляция > 0.99")
    elif correlation > 0.95:
        print("⚠️  Небольшая потеря точности. Корреляция > 0.95")
    else:
        print("❌ Значительная потеря точности!")
    
    return {
        'mae': float(mae),
        'mse': float(mse),
        'max_diff': float(max_diff),
        'correlation': float(correlation)
    }


def create_optimization_report(size_comparison, original_bench, quantized_bench, accuracy):
    """Создание итогового отчета об оптимизации"""
    
    speedup = original_bench['mean_ms'] / quantized_bench['mean_ms']
    
    report = {
        'size_reduction': size_comparison,
        'performance': {
            'original': original_bench,
            'quantized': quantized_bench,
            'speedup': float(speedup)
        },
        'accuracy': accuracy
    }
    
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ОБ ОПТИМИЗАЦИИ")
    print("=" * 60)
    
    print("\n📦 Размер модели:")
    print(f"  Уменьшение: {size_comparison['reduction_percent']:.1f}%")
    print(f"  {size_comparison['original_size_mb']:.2f} MB → {size_comparison['quantized_size_mb']:.2f} MB")
    
    print("\n⚡ Производительность:")
    print(f"  Ускорение: {speedup:.2f}x")
    print(f"  {original_bench['mean_ms']:.4f} ms → {quantized_bench['mean_ms']:.4f} ms")
    
    print("\n🎯 Точность:")
    print(f"  Корреляция: {accuracy['correlation']:.6f}")
    print(f"  MAE: {accuracy['mae']:.6f}")
    
    # Сохранение отчета
    with open('../../models/optimization/optimization_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n✅ Отчет сохранен: models/optimization/optimization_report.json")
    
    return report


def main():
    """Основная функция оптимизации"""
    
    print("=" * 60)
    print("ОПТИМИЗАЦИЯ МОДЕЛИ: КВАНТИЗАЦИЯ")
    print("=" * 60)
    
    # Пути к файлам
    ORIGINAL_MODEL = '../../models/onnx/credit_scoring_model.onnx'
    QUANTIZED_MODEL = '../../models/optimization/credit_scoring_quantized.onnx'
    
    # Проверка наличия оригинальной модели
    import os
    if not os.path.exists(ORIGINAL_MODEL):
        print(f"❌ ONNX модель не найдена: {ORIGINAL_MODEL}")
        print("Сначала запустите: python models/onnx/convert_to_onnx.py")
        return
    
    # 1. Квантизация
    quantize_onnx_model(ORIGINAL_MODEL, QUANTIZED_MODEL)
    
    # 2. Сравнение размеров
    size_comparison = compare_model_sizes(ORIGINAL_MODEL, QUANTIZED_MODEL)
    
    # 3. Бенчмарк оригинальной модели
    original_bench = benchmark_inference(
        ORIGINAL_MODEL,
        "Оригинальная модель (FP32)",
        n_samples=100,
        n_runs=1000
    )
    
    # 4. Бенчмарк квантизованной модели
    quantized_bench = benchmark_inference(
        QUANTIZED_MODEL,
        "Квантизованная модель (INT8)",
        n_samples=100,
        n_runs=1000
    )
    
    # 5. Проверка точности
    accuracy = validate_accuracy(ORIGINAL_MODEL, QUANTIZED_MODEL, n_samples=1000)
    
    # 6. Итоговый отчет
    create_optimization_report(size_comparison, original_bench, quantized_bench, accuracy)
    
    print("\n" + "=" * 60)
    print("✅ ОПТИМИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print(f"\n📁 Файлы:")
    print(f"  - Квантизованная модель: {QUANTIZED_MODEL}")
    print(f"  - Отчет: models/optimization/optimization_report.json")
    
    print("\n💡 Следующий шаг: создайте Terraform конфигурацию")
    print("   cd infrastructure/environments/production")
    print("   terraform init")


if __name__ == "__main__":
    main()
