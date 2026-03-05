FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=on \
    APP_HOME=/app
WORKDIR $APP_HOME

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

ARG DJANGO_SETTINGS_MODULE=saas.settings
ENV DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

RUN python manage.py collectstatic --noinput

EXPOSE 8000

HEALTHCHECK CMD curl -f http://localhost:8000/health/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "saas.wsgi:application"]