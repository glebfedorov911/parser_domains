# Базовый образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей requirements.txt в контейнер
COPY siteparsershops/requirements.txt .

# Создаем виртуальное окружение и устанавливаем зависимости
RUN python -m venv venv && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

RUN ls -la ./venv/bin/

# Копируем только директорию с проектом в контейнер
COPY siteparsershops/ ./siteparsershops/

# Устанавливаем переменные окружения для Django
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=siteparsershops.settings \
    HOST=0.0.0.0

WORKDIR /app/siteparsershops

# Применяем миграции с активированным виртуальным окружением
RUN ./venv/bin/python manage.py makemigrations && \
    ./venv/bin/python manage.py migrate

# Открываем порт для приложения
EXPOSE 8000

# Запускаем приложение через Uvicorn
CMD ["./venv/bin/python", "-m", "uvicorn", "siteparsershops.asgi:application", "--host", "0.0.0.0", "--port", "8000"]