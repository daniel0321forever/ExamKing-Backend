from django.urls import path
from gaming.views import *

urlpatterns = [
    path('record', Record.as_view()),
    path('auth', AuthGoogle.as_view()),
    path('signup', UserSignUp.as_view()),
    path('login', UserLogin.as_view()),
    path('token_login', TokenLogin.as_view()),
    path('user', UserAPI.as_view()),
    path('check_username', CheckUsername.as_view()),
    path('check_email', CheckEmail.as_view()),
]
