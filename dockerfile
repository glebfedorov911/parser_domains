# Базовый образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем виртуальное окружение
RUN python3 -m venv venv

# Активируем виртуальное окружение и обновляем pip
RUN . venv/bin/activate && pip install --upgrade pip

# Скопируем файл зависимостей requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только директорию с проектом в контейнер
COPY siteparsershops/ ./siteparsershops/

# Устанавливаем переменные окружения для Django
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=siteparsershops.settings \
    HOST=0.0.0.0

RUN cd siteparsershops

# Применяем миграции
RUN python manage.py makemigrations
RUN python manage.py migrate

# Открываем порт для приложения
EXPOSE 8000

# Запускаем приложение через Uvicorn
CMD ["uvicorn", "siteparsershops.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
