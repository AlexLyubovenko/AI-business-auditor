# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт для Streamlit
EXPOSE 8501

# Запускаем Streamlit приложение
CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]