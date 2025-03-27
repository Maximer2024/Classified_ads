import logging
import random
from datetime import timedelta
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from allauth.account.views import SignupView
from .models import CustomUser
from .forms import VerificationForm, ProfileForm
from .utils import send_verification_email
from ads.models import AuthorSubscription, CategorySubscription, CATEGORY_CHOICES, Ad
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.timezone import now

logger = logging.getLogger(__name__)

class CustomSignupView(SignupView):
    def form_valid(self, form):
        email = form.cleaned_data["email"]

        existing_user = CustomUser.objects.filter(email=email).first()

        if existing_user:
            if existing_user.is_email_verified:
                reset_password_url = reverse("account_reset_password")
                message = (
                    f"Этот email уже зарегистрирован. "
                    f"<a href='{reset_password_url}' style='color: blue;'>Забыли пароль?</a>"
                )
                messages.error(self.request, message)
                return redirect("account_login")

            existing_user.delete()
            logger.info(f"❌ Удалён неподтверждённый пользователь с email {email}")

        response = super().form_valid(form)
        user = self.user

        if not user:
            logger.error("❌ Ошибка при создании пользователя через SignupView")
            return redirect("account_signup")

        user.is_active = False
        user.is_email_verified = False
        user.generate_verification_code()
        user.save()

        self.request.session["unverified_email"] = user.email
        send_verification_email(user)

        logger.info(f"📩 Код подтверждения отправлен на {user.email}")

        messages.info(self.request, "На вашу почту отправлен код подтверждения. Введите его ниже.")
        return redirect(reverse("verify_email"))


def verify_email(request):
    logger.info("▶️ verify_email вызван")

    email = request.session.get("unverified_email")
    if request.user.is_authenticated:
        email = request.user.email

    if not email:
        messages.error(request, "Ошибка: сначала зарегистрируйтесь.")
        return redirect("account_signup")

    threshold = now() - timedelta(minutes=30)
    deleted_count, _ = CustomUser.objects.filter(is_email_verified=False, date_joined__lt=threshold).delete()

    if deleted_count > 0:
        logger.info(f"⏳ Автоудаление {deleted_count} неподтверждённых пользователей")

    if request.method == "POST":
        form = VerificationForm(request.POST)
        if form.is_valid():
            entered_email = form.cleaned_data["email"]
            code = form.cleaned_data["code"]

            logger.info(f"🔍 Проверка email {entered_email} и кода {code}")

            try:
                user = CustomUser.objects.get(email=entered_email, verification_code=code)
            except CustomUser.DoesNotExist:
                messages.error(request, "Неверный код или email. Попробуйте снова.")
                logger.warning(f"❌ Неверный код: email={entered_email}, код={code}")
                return redirect("verify_email")

            if not user.is_email_verified:
                user.is_active = True
                user.is_email_verified = True
                user.verification_code = None
                user.save()

                logger.info(f"✅ Email {user.email} подтверждён.")

            request.session.pop("verification_code", None)
            request.session.pop("unverified_email", None)

            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)

            messages.success(request, "Email успешно подтверждён и аккаунт активирован!")
            return redirect(reverse("user_profile"))

    else:
        form = VerificationForm(initial={"email": email})

    return render(request, "account/verify_email.html", {"form": form, "email": email})


def custom_email_verification_sent(request):
    return render(request, "account/verification_sent.html")


@require_POST
def resend_verification_code(request):
    email = request.POST.get("email")

    if not email:
        return JsonResponse({"success": False, "message": "Ошибка: Email не указан"}, status=400)

    if CustomUser.objects.filter(email=email).exists():
        reset_password_url = reverse("account_reset_password")
        message = (
            f"Этот email уже зарегистрирован. "
            f"<a href='{reset_password_url}' style='color: blue;'>Забыли пароль?</a>"
        )
        return JsonResponse({"success": False, "message": message}, status=400)

    try:
        user = CustomUser.objects.get(email=request.session.get("unverified_email"))
    except CustomUser.DoesNotExist:
        return JsonResponse({"success": False, "message": "Ошибка: пользователь не найден"}, status=400)

    user.email = email
    new_code = str(random.randint(100000, 999999))
    user.verification_code = new_code

    try:
        user.save(update_fields=["email", "verification_code"])
    except IntegrityError:
        reset_password_url = reverse("account_reset_password")
        message = (
            f"Этот email уже зарегистрирован. "
            f"<a href='{reset_password_url}' style='color: blue;'>Забыли пароль?</a>"
        )
        return JsonResponse({"success": False, "message": message}, status=400)

    send_mail(
        "Повторная отправка кода подтверждения",
        f"Ваш новый код подтверждения: {new_code}",
        "noreply@example.com",
        [email],
    )

    return JsonResponse({"success": True, "message": "Код успешно отправлен!"})

@login_required
def user_profile(request):
    latest_ads = Ad.objects.filter(author=request.user).order_by('-created_at')[:3]
    total_ads = Ad.objects.filter(author=request.user).count()
    return render(request, 'users/profile.html', {'latest_ads': latest_ads, 'total_ads': total_ads})


@login_required
def edit_profile(request):
    user = request.user
    logger.info(f"Текущий nickname перед редактированием: {user.nickname}")

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            nickname = form.cleaned_data.get('nickname')
            logger.info(f"Новый nickname из формы: {nickname}")

            if nickname and not validate_username(nickname, user):
                messages.error(request, "Этот никнейм запрещен!")
                return redirect('edit_profile')

            form.save()
            user.refresh_from_db()
            logger.info(f"Обновленный nickname в БД: {user.nickname}")

            messages.success(request, "Профиль успешно обновлен!")
            return redirect('user_profile')
        else:
            logger.warning(f"Форма недействительна: {form.errors}")
    else:
        form = ProfileForm(instance=user)

    return render(request, 'users/edit_profile.html', {'form': form})


def validate_username(username, user):
    if user.is_superuser:
        return True
    forbidden_names = ['admin', 'Admin', 'admin1', 'Admin1', 'administrator', 'root']
    return username not in forbidden_names


@login_required
def manage_subscriptions(request):
    author_subs = AuthorSubscription.objects.filter(user=request.user)
    category_subs = CategorySubscription.objects.filter(user=request.user)
    subscribed_categories = [sub.category for sub in category_subs]
    all_categories = CATEGORY_CHOICES

    return render(request, 'users/manage_subscriptions.html', {
        'author_subs': author_subs,
        'category_subs': category_subs,
        'subscribed_categories': subscribed_categories,
        'all_categories': all_categories,
    })


@require_POST
@login_required
def subscribe_category(request):
    category = request.POST.get('category')
    if category not in dict(CATEGORY_CHOICES).keys():
        messages.error(request, "Выбранная категория не существует.")
        return redirect('manage_subscriptions')

    sub, created = CategorySubscription.objects.get_or_create(
        user=request.user,
        category=category
    )
    if not created:
        sub.delete()
        messages.info(request, f"Вы отписались от категории {category}.")
    else:
        messages.success(request, f"Вы подписались на новые объявления в категории {category}.")
    return redirect('manage_subscriptions')


@login_required
@require_POST
def unsubscribe_category(request, subscription_id):
    sub = get_object_or_404(CategorySubscription, id=subscription_id, user=request.user)
    sub.delete()
    messages.success(request, "Вы успешно отписались от этой категории.")
    return redirect('manage_subscriptions')


@login_required
@require_POST
def unsubscribe_author(request, subscription_id):
    sub = get_object_or_404(AuthorSubscription, id=subscription_id, user=request.user)
    sub.delete()
    messages.success(request, "Вы успешно отписались от этого автора.")
    return redirect('manage_subscriptions')

def custom_authenticate(request, email, password):
    user = CustomUser.objects.filter(email=email).first()

    if user and not user.is_email_verified:
        user.delete()
        messages.error(request, "Вы не подтвердили email. Повторите регистрацию.")
        return redirect("account_signup")

    return authenticate(request, email=email, password=password)


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = CustomUser.objects.filter(email=email).first()

        if user and not user.is_email_verified:
            user.delete()
            messages.error(request, "Вы не подтвердили email. Повторите регистрацию.")
            return redirect("account_signup")

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("user_profile")
        else:
            messages.error(request, "Неверный email или пароль.")

    return render(request, "account/login.html")

