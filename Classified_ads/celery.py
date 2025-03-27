import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classified_ads.settings')

app = Celery('classified_ads')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "delete_unverified_users_every_30_min": {
        "task": "users.tasks.delete_old_unverified_users",
        "schedule": crontab(minute="*/30"),
    },
}
