from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from . import models
from django.core.validators import MaxValueValidator, MinValueValidator

class ProfileForm(forms.ModelForm):


    def __init__(self, *args, **kwargs):
        GENDER_CHOICES = (
        (1,'男性'),
        (2,'女性'),
        (3,'その他'),
        )
        super().__init__(*args,**kwargs)
        self.fields['gender'].widget = forms.RadioSelect(attrs = {'class' : 'form'}, choices = GENDER_CHOICES)

    class Meta:
        model = models.ProfileModel
        fields = ('nickname', 'gender', 'favarite_anime', 'avator')

class ReviewForm(forms.Form):
    anime = forms.CharField(max_length = 100)
    review = forms.CharField(max_length = 2000)
    eva_senario = forms.IntegerField(
        validators = [MinValueValidator(1),MaxValueValidator(5)]
    )
    eva_drawing = forms.IntegerField(
        validators = [MinValueValidator(1),MaxValueValidator(5)]
    )
    eva_music = forms.IntegerField(
        validators = [MinValueValidator(1),MaxValueValidator(5)]
    )
    eva_character = forms.IntegerField(
        validators = [MinValueValidator(1),MaxValueValidator(5)]
    )
    eva_cv = forms.IntegerField(
        validators = [MinValueValidator(1),MaxValueValidator(5)]
    )

class CreateComment(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ('comment',)

class CreateReply(forms.ModelForm):
    class Meta:
        model = models.ReplyComment
        fields = ('reply',)

class CSVUpload(forms.Form):
    file = forms.FileField(label = 'CSVファイル', help_text = '拡張子CSVのファイルをアップロードしてください')

    





