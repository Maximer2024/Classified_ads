from allauth.account.forms import SignupForm, LoginForm
from django.contrib.auth import get_user_model
from django import forms
from .utils import generate_verification_code, send_verification_email
from .models import CustomUser

User = get_user_model()

class CustomSignupForm(SignupForm):
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Этот email уже зарегистрирован. Если забыли пароль, "
                "воспользуйтесь <a href='/accounts/password/reset/'>восстановлением пароля</a>."
            )
        return email

    def save(self, request):
        user = super().save(request)
        user.is_active = False
        user.verification_code = generate_verification_code()
        user.save()
        send_verification_email(user)
        return user


class VerificationForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Введите ваш email'}))
    code = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'placeholder': 'Введите код'}))


class CustomLoginForm(LoginForm):
    def clean_login(self):
        email = self.cleaned_data.get("login")
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Email не найден. <a href='/accounts/signup/'>Зарегистрируйтесь</a>.",
                code='email_not_found'
            )
        return email


class ProfileForm(forms.ModelForm):
    nickname = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Введите новый никнейм'}),
        empty_value=None
    )

    class Meta:
        model = CustomUser
        fields = ['avatar', 'nickname']

    def save(self, commit=True):
        user = self.instance
        print("Очистка данных формы:", self.cleaned_data)

        avatar = self.cleaned_data.get('avatar')
        nickname = self.cleaned_data.get('nickname')

        if nickname is None:
            print("Ошибка: nickname был пустым, исправляем на None!")
            nickname = user.nickname

        update_fields = []
        if avatar:
            user.avatar = avatar
            update_fields.append('avatar')
        if nickname is not None:
            user.nickname = nickname
            update_fields.append('nickname')

        if update_fields:
            print(f"Сохранение полей: {update_fields}")
            user.save(update_fields=update_fields)

        user.refresh_from_db()
        return user