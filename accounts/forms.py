from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from . import models
from django.core.validators import MaxValueValidator, MinValueValidator

#################User info.#######################
class LoginForm(AuthenticationForm):
    """ログインフォーム"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class UserCreateForm(UserCreationForm):
    class Meta:
        model = models.User
        fields = ('email',)

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_emial(self):
        email = self.cleaned_data['email']
        User.objects.filter(email = email, is_active = False).delete()
        return email


