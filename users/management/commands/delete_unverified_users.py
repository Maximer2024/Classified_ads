from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from users.models import CustomUser
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Удаляет пользователей, которые не подтвердили email в течение 30 минут"

    def handle(self, *args, **kwargs):
        threshold = now() - timedelta(minutes=30)

        unverified_users = CustomUser.objects.filter(is_email_verified=False)
        self.stdout.write(self.style.WARNING(f"🔍 Найдено неподтвержденных пользователей: {unverified_users.count()}"))

        old_unverified_users = unverified_users.filter(date_joined__lt=threshold)
        self.stdout.write(self.style.WARNING(f"🔍 Старые неподтверждённые (>30 мин): {old_unverified_users.count()}"))

        if old_unverified_users.exists():
            count = old_unverified_users.count()
            logger.info(f"🗑 Удаление {count} неподтвержденных пользователей")
            old_unverified_users.delete()
            self.stdout.write(self.style.SUCCESS(f"✅ Удалено {count} неподтвержденных пользователей"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Нет неподтвержденных пользователей для удаления"))
