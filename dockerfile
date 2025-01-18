FROM python:3.12-slim

WORKDIR /app

COPY siteparsershops/requirements.txt .

RUN python -m venv venv && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

COPY siteparsershops/ .

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=siteparsershops.settings \
    HOST=0.0.0.0 \
    PYTHONPATH=/app

EXPOSE 8000

CMD ["sh", "-c", \
    "./venv/bin/python manage.py migrate parser 0018_uploaddatamodel_it_was_good --fake && \
    ./venv/bin/python manage.py makemigrations parser && \
    ./venv/bin/python manage.py migrate --noinput && \
    ./venv/bin/python -m uvicorn siteparsershops.asgi:application --host 0.0.0.0 --port 8000"]
