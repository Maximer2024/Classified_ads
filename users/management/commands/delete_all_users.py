from django.core.management.base import BaseCommand
from users.models import CustomUser
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Удаляет всех пользователей, кроме суперпользователей"

    def handle(self, *args, **kwargs):
        users_to_delete = CustomUser.objects.exclude(is_superuser=True)

        if not users_to_delete.exists():
            self.stdout.write(self.style.WARNING("⚠ Нет пользователей для удаления"))
            return

        deleted_users_info = list(users_to_delete.values_list("id", "email"))

        deleted_count, _ = users_to_delete.delete()

        logger.info(f"🗑 Удалено {deleted_count} пользователей (кроме суперпользователей)")
        self.stdout.write(self.style.SUCCESS(f"✅ Удалено {deleted_count} пользователей"))

        for user_id, email in deleted_users_info:
            self.stdout.write(self.style.NOTICE(f"Удалён пользователь: ID={user_id}, Email={email}"))
