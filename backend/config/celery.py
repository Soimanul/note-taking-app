import os
from celery import Celery

# Ensures Celery worker knows how to  interact with the Django Project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Creates celery app instance
app = Celery("config")

# Ensures all celery related config keys in settings.py should have a 'CELERY_' prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Will allow Celery to auto load task all task modules from the Django app
app.autodiscover_tasks()
