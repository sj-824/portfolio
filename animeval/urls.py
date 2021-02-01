from django.contrib import admin
from django.urls import path
from . import views

app_name = 'animeval'

urlpatterns = [
    path('create_profile', views.CreateProfile.as_view(), name = 'create_profile'),
    path('update_profile/<int:pk>', views.UpdateProfile.as_view(), name = 'update_profile'),
    path('home', views.Home.as_view(), name = 'home'),
    path('mypage/<int:pk>', views.MyPage.as_view(), name = 'mypage'),
    path('anime_list/<str:char>',views.AnimeList.as_view(), name = 'anime_list'),
    path('create_review', views.create_review, name = 'create_review'),
    path('review_detail/<int:pk>', views.review_detail, name = 'review_detail'),
    path('image/<int:pk>',views.get_svg2, name = 'image'),
    path('trend_image/<int:pk>',views.get_svg, name = 'trend_image'),
    path('create_comment/<int:pk>', views.create_comment, name = 'create_comment'),
    path('create_reply/<int:pk>', views.create_reply, name = 'create_reply'),
    path('delete_review/<int:pk>', views.DeleteReview.as_view(), name = 'delete_review'),
    path('update_review/<int:pk>', views.update_review, name = 'update_review'),
    path('like/<int:review_id>/<user_id>',views.like, name = 'like'),
]