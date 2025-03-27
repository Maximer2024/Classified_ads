import logging
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from ads.models import Ad, CategorySubscription, AuthorSubscription

logger = logging.getLogger(__name__)


@shared_task
def send_weekly_newsletter():
    one_week_ago = timezone.now() - timedelta(days=7)

    for sub in CategorySubscription.objects.select_related("user"):
        ads = Ad.objects.filter(category=sub.category, created_at__gte=one_week_ago)

        if ads.exists():
            message = "\n\n".join([f"{ad.title}: {ad.description}" for ad in ads])

            try:
                send_mail(
                    subject=f"Новые объявления в категории {sub.category}",
                    message=message,
                    from_email="your-email@gmail.com",
                    recipient_list=[sub.user.email],
                    fail_silently=False,
                )
                logger.info(f"✅ Рассылка категории {sub.category} отправлена {sub.user.email}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки email для {sub.user.email}: {e}")


@shared_task
def send_weekly_author_digest():
    one_week_ago = timezone.now() - timedelta(days=7)
    new_ads = Ad.objects.filter(created_at__gte=one_week_ago)

    for sub in AuthorSubscription.objects.select_related("user", "author"):
        ads_from_author = new_ads.filter(author=sub.author)

        if ads_from_author.exists():
            message = "\n\n".join([f"{ad.title}: {ad.description}" for ad in ads_from_author])

            try:
                send_mail(
                    subject=f"Новые объявления от {sub.author.get_display_name()}",
                    message=message,
                    from_email="your-email@gmail.com",
                    recipient_list=[sub.user.email],
                    fail_silently=False,
                )
                logger.info(f"✅ Рассылка объявлений от {sub.author} отправлена {sub.user.email}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки email для {sub.user.email}: {e}")


@shared_task
def notify_author_ad(ad_id):
    try:
        ad = Ad.objects.select_related("author").get(id=ad_id)
        if not ad.author:
            logger.warning(f"⚠️ У объявления {ad_id} нет автора.")
            return
    except Ad.DoesNotExist:
        logger.error(f"❌ Объявление с ID {ad_id} не найдено.")
        return

    logger.info(f"🔔 Уведомление о новом объявлении {ad.id} от {ad.author}")

    subscribers = list(AuthorSubscription.objects.filter(author=ad.author)
                       .values_list("user__email", flat=True))

    if subscribers:
        try:
            send_mail(
                subject=f"Новое объявление от {ad.author.get_display_name()}",
                message=(
                    f"Автор {ad.author.get_display_name()} опубликовал новое объявление:\n\n"
                    f"Заголовок: {ad.title}\n\nОписание: {ad.description}\n\n"
                    f"Ссылка: http://127.0.0.1:8000/ads/{ad.id}"
                ),
                from_email="your-email@gmail.com",
                recipient_list=subscribers,
                fail_silently=False,
            )
            logger.info(f"✅ Уведомления о новом объявлении {ad.id} отправлены {len(subscribers)} подписчикам")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки email о новом объявлении {ad.id}: {e}")
