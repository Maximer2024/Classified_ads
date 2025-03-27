from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if not user.is_email_verified:
            return resolve_url("verify_email")
        return super().get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        return resolve_url("verify_email")
