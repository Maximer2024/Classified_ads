import random
import string
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.apps import apps
from django.db.models import Count, Q

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('У пользователя должен быть email')

        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False, verbose_name="Email")
    username = models.CharField(max_length=150, unique=True, blank=True, null=True, verbose_name="Имя пользователя")
    is_email_verified = models.BooleanField(default=False, verbose_name="Email подтвержден")
    verification_code = models.CharField(max_length=6, blank=True, null=True, verbose_name="Код подтверждения")

    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name="Никнейм")

    category = models.CharField(
        max_length=50,
        choices=[
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
        ],
        blank=True,
        null=True,
        verbose_name="Категория"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def generate_verification_code(self):
        self.verification_code = ''.join(random.choices(string.digits, k=6))
        self.save()

    def unread_responses_count(self):
        Response = apps.get_model('ads', 'Response')
        return self.ads.annotate(
            unread_count=Count('responses', filter=Q(responses__status='pending'))
        ).aggregate(total=Count('responses'))['total'] or 0

    def get_display_name(self):
        return self.nickname if self.nickname else self.email

    def __str__(self):
        return self.get_display_name()
