"""
Обучение нейронной сети для кредитного скоринга
Этап 1: Подготовка модели к промышленной эксплуатации
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
from pathlib import Path

# Создаем директории для сохранения моделей
Path("../../models/trained").mkdir(parents=True, exist_ok=True)


class CreditScoringDataset(Dataset):
    """Датасет для кредитного скоринга"""
    
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class CreditScoringNN(nn.Module):
    """
    Fully Connected Neural Network для кредитного скоринга
    Архитектура: 3 скрытых слоя с Batch Normalization и Dropout
    """
    
    def __init__(self, input_size, hidden_sizes=[128, 64, 32], dropout_rate=0.3):
        super(CreditScoringNN, self).__init__()
        
        # Входной слой
        self.fc1 = nn.Linear(input_size, hidden_sizes[0])
        self.bn1 = nn.BatchNorm1d(hidden_sizes[0])
        self.dropout1 = nn.Dropout(dropout_rate)
        
        # Скрытый слой 2
        self.fc2 = nn.Linear(hidden_sizes[0], hidden_sizes[1])
        self.bn2 = nn.BatchNorm1d(hidden_sizes[1])
        self.dropout2 = nn.Dropout(dropout_rate)
        
        # Скрытый слой 3
        self.fc3 = nn.Linear(hidden_sizes[1], hidden_sizes[2])
        self.bn3 = nn.BatchNorm1d(hidden_sizes[2])
        self.dropout3 = nn.Dropout(dropout_rate)
        
        # Выходной слой
        self.fc4 = nn.Linear(hidden_sizes[2], 1)
        
        # Функция активации
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        # Слой 1
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)
        
        # Слой 2
        x = self.fc2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.dropout2(x)
        
        # Слой 3
        x = self.fc3(x)
        x = self.bn3(x)
        x = self.relu(x)
        x = self.dropout3(x)
        
        # Выходной слой
        x = self.fc4(x)
        x = self.sigmoid(x)
        
        return x


def load_and_preprocess_data(data_path=None):
    """
    Загрузка и предобработка данных
    Если данных нет - создаем синтетические для демонстрации
    """
    
    if data_path and os.path.exists(data_path):
        df = pd.read_csv(data_path)
    else:
        # Создаем синтетические данные для демонстрации
        print("⚠️  Создаем синтетические данные для демонстрации...")
        np.random.seed(42)
        n_samples = 10000
        
        df = pd.DataFrame({
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
        })
        
        # Создаем целевую переменную (вероятность дефолта)
        default_prob = (
            -0.02 * df['age'] +
            -0.00001 * df['income'] +
            0.00002 * df['loan_amount'] +
            -0.01 * df['credit_history_length'] +
            0.03 * df['num_late_payments'] +
            0.5 * df['debt_to_income'] +
            0.1 * df['credit_utilization'] +
            np.random.normal(0, 0.1, n_samples)
        )
        df['default'] = (1 / (1 + np.exp(-default_prob)) > 0.5).astype(int)
    
    # Разделение на признаки и целевую переменную
    X = df.drop('default', axis=1).values
    y = df['default'].values.reshape(-1, 1)
    
    # Разделение на train/val/test
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    # Стандартизация
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)
    
    # Сохраняем scaler для дальнейшего использования
    joblib.dump(scaler, '../../models/trained/scaler.pkl')
    
    return X_train, X_val, X_test, y_train, y_val, y_test


def train_model(model, train_loader, val_loader, epochs=50, lr=0.001, device='cpu'):
    """Обучение модели"""
    
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', patience=5, factor=0.5, verbose=True
    )
    
    model.to(device)
    best_val_loss = float('inf')
    
    history = {
        'train_loss': [],
        'val_loss': [],
        'train_acc': [],
        'val_acc': []
    }
    
    for epoch in range(epochs):
        # Обучение
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            predictions = (outputs >= 0.5).float()
            train_correct += (predictions == y_batch).sum().item()
            train_total += y_batch.size(0)
        
        # Валидация
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                outputs = model(X_batch)
                loss = criterion(outputs, y_batch)
                
                val_loss += loss.item()
                predictions = (outputs >= 0.5).float()
                val_correct += (predictions == y_batch).sum().item()
                val_total += y_batch.size(0)
        
        # Метрики
        train_loss = train_loss / len(train_loader)
        val_loss = val_loss / len(val_loader)
        train_acc = train_correct / train_total
        val_acc = val_correct / val_total
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)
        
        # Вывод прогресса
        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{epochs}]')
            print(f'  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}')
            print(f'  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}')
        
        # Сохранение лучшей модели
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
            }, '../../models/trained/best_model.pth')
        
        # Scheduler
        scheduler.step(val_loss)
    
    return history


def evaluate_model(model, test_loader, device='cpu'):
    """Оценка модели на тестовых данных"""
    
    model.eval()
    model.to(device)
    
    correct = 0
    total = 0
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            outputs = model(X_batch)
            predictions = (outputs >= 0.5).float()
            
            correct += (predictions == y_batch).sum().item()
            total += y_batch.size(0)
            
            all_predictions.extend(predictions.cpu().numpy())
            all_targets.extend(y_batch.cpu().numpy())
    
    accuracy = correct / total
    
    # Дополнительные метрики
    from sklearn.metrics import classification_report, roc_auc_score
    
    print("\n=== Результаты на тестовом наборе ===")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"ROC-AUC: {roc_auc_score(all_targets, all_predictions):.4f}")
    print("\nClassification Report:")
    print(classification_report(all_targets, all_predictions))
    
    return accuracy


def main():
    """Основная функция обучения"""
    
    print("🚀 Начинаем обучение модели кредитного скоринга...")
    
    # Параметры
    BATCH_SIZE = 64
    EPOCHS = 50
    LEARNING_RATE = 0.001
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"📱 Используем устройство: {DEVICE}")
    
    # Загрузка данных
    print("\n📊 Загрузка и предобработка данных...")
    X_train, X_val, X_test, y_train, y_val, y_test = load_and_preprocess_data()
    
    print(f"  Train set: {X_train.shape[0]} samples")
    print(f"  Val set: {X_val.shape[0]} samples")
    print(f"  Test set: {X_test.shape[0]} samples")
    print(f"  Features: {X_train.shape[1]}")
    
    # Создание DataLoader
    train_dataset = CreditScoringDataset(X_train, y_train)
    val_dataset = CreditScoringDataset(X_val, y_val)
    test_dataset = CreditScoringDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    # Создание модели
    print("\n🧠 Создание нейронной сети...")
    model = CreditScoringNN(input_size=X_train.shape[1])
    print(model)
    
    # Обучение
    print("\n🎓 Начинаем обучение...")
    history = train_model(
        model, train_loader, val_loader,
        epochs=EPOCHS, lr=LEARNING_RATE, device=DEVICE
    )
    
    # Загрузка лучшей модели
    print("\n📥 Загрузка лучшей модели...")
    checkpoint = torch.load('../../models/trained/best_model.pth')
    model.load_state_dict(checkpoint['model_state_dict'])
    
    # Оценка
    evaluate_model(model, test_loader, device=DEVICE)
    
    # Сохранение финальной модели для ONNX конвертации
    model.eval()
    torch.save(model, '../../models/trained/credit_scoring_nn.pth')
    
    print("\n✅ Обучение завершено!")
    print(f"✅ Модель сохранена в: models/trained/")
    print(f"✅ Scaler сохранен в: models/trained/scaler.pkl")
    
    return model, history


if __name__ == "__main__":
    model, history = main()
