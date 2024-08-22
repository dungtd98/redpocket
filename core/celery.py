from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.beat_schedule = {
    'create-daily-stake-everyday': {
        'task': 'wallet.tasks.create_daily_stake',
        'schedule': crontab(minute=0, hour=0)
    },
}

app.autodiscover_tasks()
app.conf.timezone = settings.TIME_ZONE
app.conf.enable_utc = False