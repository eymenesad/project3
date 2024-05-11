from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User

class CustomUserLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')
