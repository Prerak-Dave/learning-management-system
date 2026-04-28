"""
celery.py - Celery application entry point.

Place this file alongside settings.py (i.e., in the same directory as manage.py
or inside your project package, next to settings.py).

Usage:
    celery -A <project_name> worker -l info
    celery -A <project_name> beat -l info   # if you add periodic tasks later
"""

import os

from celery import Celery

# Point Celery at the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("lms")

# Read configuration from Django's settings, using the CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


