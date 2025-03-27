from apscheduler.schedulers.background import BackgroundScheduler
from .tasks import send_weekly_newsletter
from celery import shared_task
from django.utils.timezone import now
from datetime import timedelta
from .models import CustomUser
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_weekly_newsletter, 'interval', weeks=1)
    scheduler.start()

@shared_task
def delete_old_unverified_users():
    threshold = now() - timedelta(minutes=30)
    deleted_users = CustomUser.objects.filter(is_email_verified=False, date_joined__lt=threshold)

    if deleted_users.exists():
        count = deleted_users.count()
        deleted_users.delete()
        logger.info(f"✅ Удалено {count} неподтвержденных пользователей.")
    else:
        logger.info("⚠ Нет неподтвержденных пользователей для удаления.")