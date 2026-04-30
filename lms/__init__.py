# Source - https://stackoverflow.com/a/73401366
# Posted by Jedi Knight
# Retrieved 2026-04-29, License - CC BY-SA 4.0

from .celery import app as celery_app

__all__ = ['celery_app']