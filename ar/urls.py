from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='ar_index'),
    path('ar_bets/', views.ar_bets, name='ar_bets'),
]
