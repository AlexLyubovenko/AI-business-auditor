# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем не-root пользователя для безопасности
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Открываем порты (ВАЖНО: комментарии отдельно!)
# Порт для Streamlit
EXPOSE 8501
# Порт для Health check
EXPOSE 8080

# Запускаем все сервисы через runner.py
CMD ["python", "runner.py"]