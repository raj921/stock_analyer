# Dockerfile
FROM python:3.11

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE stock_analyzer.settings

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project into the container
COPY . .

# List contents of the current directory (for debugging)
RUN ls -la /app

# Add the current directory to PYTHONPATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Run collectstatic
RUN python manage.py collectstatic --noinput || echo "Failed to run collectstatic"

# Create necessary directories
RUN mkdir -p /app/financial_data/models

# Use 8000 as the default port if $PORT is not set
CMD gunicorn stock_analyzer.wsgi:application --bind 0.0.0.0:${PORT:-8000}

# docker-compose.yml





