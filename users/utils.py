from django.core.mail import send_mail
from django.utils.crypto import get_random_string

def generate_verification_code():
    return get_random_string(length=6, allowed_chars="0123456789")

def send_verification_email(user):
    subject = "Подтверждение вашего email"
    message = f"Ваш код подтверждения: {user.verification_code}"
    send_mail(subject, message, "noreply@yourdomain.com", [user.email])