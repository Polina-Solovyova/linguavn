FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first to leverage layer caching.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY . /app

# vn_builder is mounted by docker-compose at runtime.
EXPOSE 8000

# Run migrations + seed demo + serve. Uses Django's dev server in
# DEBUG mode and gunicorn otherwise.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_demo || true; if [ \"$DJANGO_DEBUG\" = \"true\" ] || [ \"$DJANGO_DEBUG\" = \"1\" ]; then python manage.py runserver 0.0.0.0:8000; else gunicorn visual_novels.wsgi:application --bind 0.0.0.0:8000 --workers 3; fi"]
