from django.core.cache import cache
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from .models import Ad, Response, CategorySubscription, AuthorSubscription, CATEGORY_CHOICES
from .forms import AdForm, ResponseForm, CategorySubscriptionForm, AuthorSubscriptionForm

logger = logging.getLogger('ads')

def debug_ad_object(ad):
    print("DEBUG: Ad object attributes ->", dir(ad))

def home(request):
    return render(request, 'index.html')

@login_required
def ad_list(request):
    category = request.GET.get('category', '')
    search_query = request.GET.get('search', '')

    ads = Ad.objects.all().order_by('-created_at')

    if category and category != "Все категории":
        ads = ads.filter(category=category)

    if search_query:
        ads = ads.filter(title__icontains=search_query)

    unread_responses_count = (
        Response.objects.filter(ad__author=request.user, status='pending').count()
        if request.user.is_authenticated else 0
    )

    return render(request, 'ads/ad_list.html', {
        'ads': ads,
        'category_choices': CATEGORY_CHOICES,
        'selected_category': category,
        'search_query': search_query,
        'unread_responses_count': unread_responses_count,
    })


@login_required
def ad_detail(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    responses = ad.responses.all()
    images = [ad.image1, ad.image2, ad.image3] if hasattr(ad, 'image1') else []
    images = [img for img in images if img]
    subscriptions = AuthorSubscription.objects.filter(user=request.user)
    subscribed_authors = list(subscriptions.values_list('author_id', flat=True))

    return render(request, 'ads/ad_detail.html', {
        'ad': ad,
        'responses': responses,
        'images': images,
        'subscribed_authors': subscribed_authors,
    })

@login_required
def subscribe_category(request):
    if request.method == "POST":
        form = CategorySubscriptionForm(request.POST)
        if form.is_valid():
            subscription, created = CategorySubscription.objects.get_or_create(
                user=request.user,
                category=form.cleaned_data['category']
            )
            if not created:
                subscription.delete()
                messages.info(request, "Вы отписались от этой категории.")
            else:
                messages.success(request, "Вы подписались на новые объявления по категории.")
            return redirect('user_profile')
    else:
        form = CategorySubscriptionForm()

    subscriptions = CategorySubscription.objects.filter(user=request.user)
    return render(request, 'ads/subscriptions.html', {'form': form, 'subscriptions': subscriptions})

@login_required
def subscribe_author(request):
    if request.method == "POST":
        form = AuthorSubscriptionForm(request.POST)
        if form.is_valid():
            author = form.cleaned_data['author']
            if request.user == author:
                messages.error(request, "Нельзя подписываться на самого себя.")
                return redirect('user_profile')
            subscription, created = AuthorSubscription.objects.get_or_create(
                user=request.user,
                author=author
            )
            if not created:
                subscription.delete()
                messages.info(request, "Вы отписались от этого автора.")
            else:
                messages.success(request, "Вы подписались на объявления этого автора.")
            return redirect('user_profile')
    else:
        form = AuthorSubscriptionForm()

    subscriptions = AuthorSubscription.objects.filter(user=request.user)
    return render(request, 'ads/subscriptions.html', {
        'form': form,
        'subscriptions': subscriptions
    })

def notify_subscribers_on_new_ad(ad):
    print(f"DEBUG: ad.author -> {ad.author}")
    print(f"DEBUG: ad attributes -> {dir(ad)}")

    category_subscribers = CategorySubscription.objects.filter(category=ad.category).values_list('user__email', flat=True)
    author_subscribers = AuthorSubscription.objects.filter(author=ad.author).values_list('user__email', flat=True)

    recipient_list = set(category_subscribers) | set(author_subscribers)

    if recipient_list:
        send_mail(
            subject=f"Новое объявление в категории {ad.category}",
            message=f"Автор {ad.author.get_full_name() if ad.author else 'Неизвестный'} "
                    f"опубликовал новое объявление:\n\n"
                    f"{ad.title}\n\n{ad.description}\n\n"
                    f"Перейдите по ссылке: http://127.0.0.1:8000/ads/{ad.id}",
            from_email="your-email@gmail.com",
            recipient_list=list(recipient_list),
            fail_silently=False,
        )

@login_required
def ad_create(request):
    if request.method == "POST":
        form = AdForm(request.POST, request.FILES)
        if form.is_valid():
            ad = form.save(commit=False)

            if not request.user.is_authenticated:
                return HttpResponseForbidden("Вы должны быть авторизованы, чтобы создать объявление.")

            ad.author = request.user
            ad.save()

            print(f"DEBUG: request.user -> {request.user}")
            print(f"DEBUG: request.user attributes -> {dir(request.user)}")
            print(f"DEBUG: ad.author -> {ad.author}")
            print(f"DEBUG: ad attributes -> {dir(ad)}")

            notify_subscribers_on_new_ad(ad)

            messages.success(request, "Объявление успешно создано!")
            return redirect('user_profile')

    else:
        form = AdForm()
    return render(request, 'ads/ad_form.html', {'form': form})

@login_required
def add_response(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    if request.method == "POST":
        form = ResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.user = request.user
            response.ad = ad
            response.save()

            send_mail(
                subject="Новый отклик на ваше объявление",
                message=f"Пользователь {response.user.email} оставил отклик на ваше объявление '{ad.title}'.\n\n"
                        f"Текст отклика: {response.text}",
                from_email="your-email@gmail.com",
                recipient_list=[ad.author.email],
                fail_silently=False,
            )

            messages.success(request, "Ваш отклик отправлен!")
            return redirect('ad_detail', ad_id=ad.id)
    else:
        form = ResponseForm()
    return render(request, 'ads/add_response.html', {'form': form, 'ad': ad})

@login_required
def user_responses(request):
    received_responses = Response.objects.filter(ad__author=request.user).order_by('-created_at')
    my_responses = Response.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'ads/user_responses.html', {
        'received_responses': received_responses,
        'my_responses': my_responses
    })

@login_required
def change_response_status(request, response_id, status):
    response = get_object_or_404(Response, id=response_id, ad__author=request.user)

    if response.status in ['accepted', 'rejected']:
        return HttpResponseForbidden("Вы не можете изменить статус уже обработанного отклика.")

    response.status = status
    response.save()

    cache.delete(f"unread_responses_{request.user.id}")

    subject = "Ваш отклик был принят" if status == "accepted" else "Ваш отклик был отклонён"
    message = (
        f"Поздравляем! Ваш отклик на объявление '{response.ad.title}' был принят."
        if status == "accepted"
        else f"К сожалению, ваш отклик на объявление '{response.ad.title}' был отклонён."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email="your-email@gmail.com",
        recipient_list=[response.user.email],
        fail_silently=False,
    )

    messages.success(request, "Отклик принят!") if status == "accepted" else messages.warning(request, "Отклик отклонён!")
    return redirect('user_responses')

@login_required
@require_POST
def delete_response(request, response_id):
    response = get_object_or_404(Response, id=response_id)

    if response.user != request.user:
        return HttpResponseForbidden("Вы не можете удалить этот отклик!")

    response.delete()
    messages.success(request, "Отклик удалён!")
    return redirect('user_responses')

@login_required
def get_unread_responses(request):
    unread_count = Response.objects.filter(ad__author=request.user, status='pending').count()
    return JsonResponse({'unread_responses': unread_count})

@login_required
def ad_update(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id, author=request.user)
    if request.method == "POST":
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, "Объявление обновлено!")
            return redirect('ad_detail', ad_id=ad.id)
    else:
        form = AdForm(instance=ad)
    return render(request, 'ads/ad_form.html', {'form': form, 'ad': ad})

@login_required
def ad_delete(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id, author=request.user)
    if request.method == "POST":
        ad.delete()
        messages.success(request, "Объявление удалено!")
        return redirect('ad_list')
    return render(request, 'ads/ad_confirm_delete.html', {'ad': ad})

def manage_subscriptions(request):
    author_subs = AuthorSubscription.objects.filter(user=request.user)
    category_subs = CategorySubscription.objects.filter(user=request.user)

    return render(request, 'users/manage_subscriptions.html', {
        'author_subs': author_subs,
        'category_subs': category_subs,
    })

@login_required
def user_ads(request):
    ads = Ad.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'ads/user_ads.html', {'ads': ads})