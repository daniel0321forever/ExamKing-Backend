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
    path('initialize_problem', InitializeProblem.as_view()),
    path('correct_rate', CorrectRateAPI.as_view()),
    path('word_progress', WordProgressAPI.as_view()),
    path('word', WordAPI.as_view()),
]
