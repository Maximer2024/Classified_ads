from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser
from datetime import timedelta
from .models import CustomUser
from django.utils.timezone import now

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if not instance.nickname:
            instance.nickname = f"User{instance.id}"
            instance.save(update_fields=['nickname'])

@receiver(post_save, sender=CustomUser)
def delete_unverified_users(sender, instance, **kwargs):
    if not instance.is_email_verified:
        time_since_creation = now() - instance.date_joined
        if time_since_creation > timedelta(minutes=30):
            instance.delete()
            logger.info(f"⏳ Удалён неподтверждённый пользователь: {instance.email}")