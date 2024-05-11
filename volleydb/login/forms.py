from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'is_manager', 'is_player', 'is_coach', 'is_jury', 'date_of_birth', 'height', 'weight', 'nationality']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user