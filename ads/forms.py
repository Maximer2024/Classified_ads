from django import forms
from .models import Ad, Response, CategorySubscription, AuthorSubscription

class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ['title', 'description', 'image1', 'image2', 'image3', 'video_url', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'author' in self.fields:
            self.fields['author'].widget = forms.HiddenInput()

class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['text']

class CategorySubscriptionForm(forms.ModelForm):
    class Meta:
        model = CategorySubscription
        fields = ['category']

class AuthorSubscriptionForm(forms.ModelForm):
    class Meta:
        model = AuthorSubscription
        fields = ['author']
