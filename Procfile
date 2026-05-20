web: gunicorn conf.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
worker: celery -A conf worker --loglevel=info --concurrency=4
beat: celery -A conf beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
