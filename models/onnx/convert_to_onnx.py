"""
Конвертация PyTorch модели в ONNX формат
Этап 1: Подготовка модели к промышленной эксплуатации
"""

import torch
import onnx
import onnxruntime as ort
import numpy as np
import time
import joblib
from pathlib import Path

# Импортируем модель из train_nn.py
import sys
sys.path.append('../training')
from train_nn import CreditScoringNN

# Создаем директории
Path("../../models/onnx").mkdir(parents=True, exist_ok=True)


def convert_to_onnx(model_path, onnx_path, input_size=10):
    """
    Конвертация PyTorch модели в ONNX формат
    
    Args:
        model_path: путь к PyTorch модели (.pth)
        onnx_path: путь для сохранения ONNX модели (.onnx)
        input_size: размер входного тензора (количество features)
    """
    
    print("🔄 Начинаем конвертацию в ONNX...")
    
    # Загрузка PyTorch модели
    model = torch.load(model_path, map_location='cpu')
    model.eval()
    
    # Создаем dummy input для трассировки
    dummy_input = torch.randn(1, input_size)
    
    # Экспорт в ONNX
    torch.onnx.export(
        model,                          # модель
        dummy_input,                     # пример входных данных
        onnx_path,                       # путь для сохранения
        export_params=True,              # сохранить веса
        opset_version=12,                # версия ONNX opset
        do_constant_folding=True,        # оптимизация константных операций
        input_names=['input'],           # имя входа
        output_names=['output'],         # имя выхода
        dynamic_axes={                   # динамические размеры
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )
    
    print(f"✅ Модель успешно конвертирована: {onnx_path}")
    
    return onnx_path


def validate_onnx(onnx_path):
    """
    Валидация ONNX модели
    Проверяет корректность структуры модели
    """
    
    print("\n🔍 Валидация ONNX модели...")
    
    # Загрузка ONNX модели
    onnx_model = onnx.load(onnx_path)
    
    # Проверка корректности
    try:
        onnx.checker.check_model(onnx_model)
        print("✅ ONNX модель валидна!")
    except onnx.checker.ValidationError as e:
        print(f"❌ Ошибка валидации: {e}")
        return False
    
    # Вывод информации о модели
    print("\n📊 Информация о модели:")
    print(f"  IR Version: {onnx_model.ir_version}")
    print(f"  Producer: {onnx_model.producer_name}")
    print(f"  Graph nodes: {len(onnx_model.graph.node)}")
    
    # Информация о входах и выходах
    print("\n  Входы:")
    for input_tensor in onnx_model.graph.input:
        print(f"    - {input_tensor.name}: {input_tensor.type}")
    
    print("\n  Выходы:")
    for output_tensor in onnx_model.graph.output:
        print(f"    - {output_tensor.name}: {output_tensor.type}")
    
    return True


def compare_outputs(pytorch_model_path, onnx_path, test_data, scaler_path):
    """
    Сравнение выходов PyTorch и ONNX моделей
    Проверка корректности конвертации
    """
    
    print("\n🔬 Сравнение выходов PyTorch vs ONNX...")
    
    # Загрузка моделей
    pytorch_model = torch.load(pytorch_model_path, map_location='cpu')
    pytorch_model.eval()
    
    ort_session = ort.InferenceSession(onnx_path)
    
    # Загрузка scaler
    scaler = joblib.load(scaler_path)
    
    # Подготовка тестовых данных
    test_data_scaled = scaler.transform(test_data)
    test_tensor = torch.FloatTensor(test_data_scaled)
    
    # PyTorch inference
    with torch.no_grad():
        pytorch_output = pytorch_model(test_tensor).numpy()
    
    # ONNX inference
    onnx_output = ort_session.run(
        None,
        {'input': test_data_scaled.astype(np.float32)}
    )[0]
    
    # Сравнение
    max_diff = np.max(np.abs(pytorch_output - onnx_output))
    mean_diff = np.mean(np.abs(pytorch_output - onnx_output))
    
    print(f"  Максимальная разница: {max_diff:.10f}")
    print(f"  Средняя разница: {mean_diff:.10f}")
    
    if max_diff < 1e-5:
        print("✅ Выходы идентичны! Конвертация прошла успешно.")
        return True
    else:
        print("⚠️  Обнаружены различия в выходах.")
        return False


def benchmark_performance(pytorch_model_path, onnx_path, test_data, scaler_path, n_runs=1000):
    """
    Сравнение производительности PyTorch vs ONNX
    Замер времени инференса на CPU
    """
    
    print(f"\n⚡ Benchmark производительности ({n_runs} итераций)...")
    
    # Загрузка моделей
    pytorch_model = torch.load(pytorch_model_path, map_location='cpu')
    pytorch_model.eval()
    
    ort_session = ort.InferenceSession(onnx_path)
    
    # Загрузка scaler
    scaler = joblib.load(scaler_path)
    test_data_scaled = scaler.transform(test_data)
    
    # Прогрев (warm-up)
    test_tensor = torch.FloatTensor(test_data_scaled)
    with torch.no_grad():
        _ = pytorch_model(test_tensor)
    _ = ort_session.run(None, {'input': test_data_scaled.astype(np.float32)})
    
    # PyTorch benchmark
    pytorch_times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        with torch.no_grad():
            _ = pytorch_model(test_tensor)
        pytorch_times.append(time.perf_counter() - start)
    
    # ONNX benchmark
    onnx_times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        _ = ort_session.run(None, {'input': test_data_scaled.astype(np.float32)})
        onnx_times.append(time.perf_counter() - start)
    
    # Результаты
    pytorch_mean = np.mean(pytorch_times) * 1000  # в миллисекундах
    pytorch_std = np.std(pytorch_times) * 1000
    onnx_mean = np.mean(onnx_times) * 1000
    onnx_std = np.std(onnx_times) * 1000
    
    speedup = pytorch_mean / onnx_mean
    
    print("\n📊 Результаты:")
    print(f"  PyTorch:")
    print(f"    Среднее время: {pytorch_mean:.4f} ± {pytorch_std:.4f} ms")
    print(f"  ONNX:")
    print(f"    Среднее время: {onnx_mean:.4f} ± {onnx_std:.4f} ms")
    print(f"  Ускорение: {speedup:.2f}x")
    
    # Сохранение результатов
    results = {
        'pytorch_mean_ms': pytorch_mean,
        'pytorch_std_ms': pytorch_std,
        'onnx_mean_ms': onnx_mean,
        'onnx_std_ms': onnx_std,
        'speedup': speedup,
        'n_runs': n_runs
    }
    
    import json
    with open('../../models/onnx/benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


def get_model_size(model_path):
    """Получение размера модели в МБ"""
    import os
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    return size_mb


def main():
    """Основная функция конвертации и валидации"""
    
    print("=" * 60)
    print("КОНВЕРТАЦИЯ МОДЕЛИ В ONNX ФОРМАТ")
    print("=" * 60)
    
    # Пути к файлам
    PYTORCH_MODEL = '../../models/trained/credit_scoring_nn.pth'
    ONNX_MODEL = '../../models/onnx/credit_scoring_model.onnx'
    SCALER_PATH = '../../models/trained/scaler.pkl'
    INPUT_SIZE = 10
    
    # Проверка наличия PyTorch модели
    import os
    if not os.path.exists(PYTORCH_MODEL):
        print(f"❌ Модель не найдена: {PYTORCH_MODEL}")
        print("Сначала запустите: python models/training/train_nn.py")
        return
    
    # 1. Конвертация в ONNX
    convert_to_onnx(PYTORCH_MODEL, ONNX_MODEL, input_size=INPUT_SIZE)
    
    # 2. Валидация ONNX
    if not validate_onnx(ONNX_MODEL):
        print("❌ Валидация не пройдена!")
        return
    
    # 3. Сравнение размеров моделей
    print("\n📦 Размеры моделей:")
    pytorch_size = get_model_size(PYTORCH_MODEL)
    onnx_size = get_model_size(ONNX_MODEL)
    print(f"  PyTorch: {pytorch_size:.2f} MB")
    print(f"  ONNX: {onnx_size:.2f} MB")
    print(f"  Разница: {((onnx_size - pytorch_size) / pytorch_size * 100):+.1f}%")
    
    # 4. Создание тестовых данных
    np.random.seed(42)
    test_data = np.random.randn(100, INPUT_SIZE)
    
    # 5. Сравнение выходов
    compare_outputs(PYTORCH_MODEL, ONNX_MODEL, test_data, SCALER_PATH)
    
    # 6. Benchmark производительности
    benchmark_performance(PYTORCH_MODEL, ONNX_MODEL, test_data, SCALER_PATH)
    
    print("\n" + "=" * 60)
    print("✅ КОНВЕРТАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print(f"\n📁 Файлы сохранены:")
    print(f"  - ONNX модель: {ONNX_MODEL}")
    print(f"  - Результаты benchmark: models/onnx/benchmark_results.json")
    print("\n💡 Следующий шаг: запустите оптимизацию модели")
    print("   python models/optimization/quantize.py")


if __name__ == "__main__":
    main()
