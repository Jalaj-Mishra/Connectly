from django.urls import path
from . import views

urlpatterns = [
    path('', views.twitter_profile, name='twitter_profile'),
    path('login/', views.twitter_login, name='twitter_login'),
    path('callback/', views.twitter_callback, name='twitter_callback'),
    path('disconnect/', views.twitter_disconnect, name='twitter_disconnect'),
]
