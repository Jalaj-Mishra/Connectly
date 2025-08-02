from django.urls import path
from . import views

urlpatterns = [
    path('', views.linkedin_profile, name='linkedin_profile'),
    path('login/', views.linkedin_login, name='linkedin_login'),
    path('callback/', views.linkedin_callback, name='linkedin_callback'),
    path('disconnect/', views.linkedin_disconnect, name='linkedin_disconnect'),
]
