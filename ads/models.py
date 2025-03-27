from django.db import models
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
import re
from django.conf import settings
from django.template.defaultfilters import register

User = get_user_model()

CATEGORY_CHOICES = [
    ('Танки', 'Танки'),
    ('Хилы', 'Хилы'),
    ('ДД', 'ДД'),
    ('Торговцы', 'Торговцы'),
    ('Гильдмастеры', 'Гильдмастеры'),
    ('Квестгиверы', 'Квестгиверы'),
    ('Кузнецы', 'Кузнецы'),
    ('Кожевники', 'Кожевники'),
    ('Зельевары', 'Зельевары'),
    ('Мастера заклинаний', 'Мастера заклинаний'),
]

def validate_youtube_url(value):
    youtube_regex = r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    if value and not re.match(youtube_regex, value):
        raise ValidationError('Введите корректную ссылку на YouTube.')

@register.filter
def replace_youtube_url(value):
    return value.replace("watch?v=", "embed/") if value else value

class CategorySubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name="Категория")

    def __str__(self):
        return f"{self.user.email} подписан на категорию {self.category}"

class AuthorSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Подписчик", related_name="author_subscriptions")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор", related_name="followers")

    def __str__(self):
        return f"{self.user.email} подписан на {self.author.email}"

class Ad(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Текст объявления")

    image1 = models.ImageField(upload_to='ads_images/', blank=True, null=True, verbose_name="Изображение 1")
    image2 = models.ImageField(upload_to='ads_images/', blank=True, null=True, verbose_name="Изображение 2")
    image3 = models.ImageField(upload_to='ads_images/', blank=True, null=True, verbose_name="Изображение 3")

    video_url = models.URLField(blank=True, null=True, verbose_name="Видео (ссылка на YouTube)", validators=[validate_youtube_url])
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Танки', verbose_name="Категория")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ads", verbose_name="Автор")

    def __str__(self):
        return self.title


class Response(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонён'),
    ]

    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="responses", verbose_name="Объявление")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="responses", verbose_name="Автор отклика")
    text = models.TextField(verbose_name="Текст отклика")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")

    def __str__(self):
        return f"Отклик от {self.user.email} на {self.ad.title}"

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, "Неизвестный статус")

    def send_notification(self):
        if self.ad.author and self.ad.author.email:
            send_mail(
                subject=f'Новый отклик на ваше объявление: {self.ad.title}',
                message=f'Пользователь {self.user.email} оставил отклик: {self.text}\n\n'
                        f'Перейдите в личный кабинет для управления откликами.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.ad.author.email],
                fail_silently=False,
            )

    def notify_user_accepted(self):
        send_mail(
            subject='Ваш отклик принят!',
            message=f'Ваш отклик на объявление "{self.ad.title}" был принят!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.user.email],
            fail_silently=False,
        )
