from django.urls import path
from .views import (
    user_profile,
    edit_profile,
    verify_email,
    custom_email_verification_sent,
    CustomSignupView,
    manage_subscriptions,
    subscribe_category,
    unsubscribe_author,
    unsubscribe_category,
    resend_verification_code
)

urlpatterns = [
    path('profile/', user_profile, name='user_profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('verify-email/', verify_email, name='verify_email'),
    path("accounts/confirm-email/", custom_email_verification_sent, name="verification_sent"),
    path("resend-code/", resend_verification_code, name="resend_verification_code"),
    path("accounts/signup/", CustomSignupView.as_view(), name="account_signup"),
    path('subscriptions/manage/', manage_subscriptions, name='manage_subscriptions'),
    path('subscriptions/subscribe-category/', subscribe_category, name='subscribe_category'),
    path('subscriptions/unsubscribe/author/<int:subscription_id>/', unsubscribe_author, name='unsubscribe_author'),
    path('subscriptions/unsubscribe/category/<int:subscription_id>/', unsubscribe_category, name='unsubscribe_category'),
]
