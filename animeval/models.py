from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.contrib.auth.base_user import BaseUserManager
from django_mysql.models import ListCharField, ListTextField
from accounts.models import User

# Create your models here.

class ProfileModel(models.Model):

    GENDER_CHOICES = (
        (1,'男性'),
        (2,'女性'),
        (3,'その他'),
    )

    user = models.ForeignKey(User, on_delete = models.CASCADE,related_name = 'user')
    nickname = models.CharField(max_length = 10,verbose_name = 'ニックネーム')
    gender = models.IntegerField(choices = GENDER_CHOICES, blank = False)
    favarite_anime = models.CharField(max_length = 100)
    avator = models.ImageField(upload_to = 'images/', blank = False)
    

    def __str__(self):
        return self.nickname

class AnimeModel(models.Model):
    title = models.CharField(max_length = 100)
    title_kana = models.CharField(max_length = 100,default = 'None')
    started = models.CharField(max_length = 10,default = 'None')
    genre = models.CharField(max_length = 15, default= 'None')
    corporation = models.CharField (max_length = 100,default = 'None')
    character_voice = ListCharField(
        base_field = models.CharField(max_length = 20),
        size = 6,
        max_length = (6 * 21),
        default = ['None']
    )

    def __str__(self):
        return self.title

class ReviewModel(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    profile = models.ForeignKey(ProfileModel, on_delete = models.CASCADE)
    anime = models.ForeignKey(AnimeModel, on_delete = models.CASCADE)
    review_title = models.CharField(max_length =50)
    review_content = models.TextField()
    evaluation = ListTextField(
        base_field = models.IntegerField(),
        size = 5,
        default = [0,0,0,0,0]
    )
    evaluation_ave = models.DecimalField(max_digits=2, decimal_places=1)
    post_date = models.DateTimeField(auto_now_add = True)

class Counter(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    counter = ListTextField(
        base_field = models.IntegerField(),
        size = 8,
        default = [0,0,0,0,0,0,0,0]
    )

class AccessReview(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    review = models.ForeignKey(ReviewModel, on_delete = models.CASCADE)
    created_at = models.DateTimeField(default = timezone.now)

    def __str__(self):
        return 'アクセス名:{} / レビュータイトル:{}'.format(self.user.username, self.review.review_title)

class Comment(models.Model):
    comment = models.CharField(max_length = 255)
    review = models.ForeignKey(ReviewModel, on_delete = models.CASCADE)
    user = models.ForeignKey(User,on_delete = models.CASCADE)
    profile = models.ForeignKey(ProfileModel, on_delete = models.CASCADE, blank = True, default = 4)
    created_at = models.DateTimeField(auto_now_add = True)

class ReplyComment(models.Model):
    reply = models.CharField(max_length = 255)
    comment = models.ForeignKey(Comment, on_delete = models.CASCADE)
    user = models.ForeignKey(User,on_delete = models.CASCADE)
    profile = models.ForeignKey(ProfileModel, on_delete = models.CASCADE, blank = True, default = 4)
    created_at = models.DateTimeField(auto_now_add = True)

class Like(models.Model):
    review = models.ForeignKey(ReviewModel, on_delete = models.CASCADE)
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    like = models.IntegerField(default = 0)
    created_at = models.DateTimeField(auto_now_add = True)