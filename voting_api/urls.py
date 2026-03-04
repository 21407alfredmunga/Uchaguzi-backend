from django.urls import path

from .views import index, signup, login


urlpatterns = [
    path('timo/', index),
    path('register/', signup),
    path('voters/login/', login, name='voter-login'),
]