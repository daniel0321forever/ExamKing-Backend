from django.urls import path
from gaming.views import *

urlpatterns = [
    path('record', Record.as_view()),
    path('auth', AuthGoogle.as_view()),
]