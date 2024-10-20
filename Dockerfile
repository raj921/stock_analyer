FROM python:3.11

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE stock_analyzer.settings

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG SECRET_KEY
ENV SECRET_KEY=${SECRET_KEY}

RUN python manage.py collectstatic --noinput || echo "Failed to run collectstatic"

RUN mkdir -p /app/financial_data/models

CMD gunicorn stock_analyzer.wsgi:application --bind 0.0.0.0:${PORT:-8000}