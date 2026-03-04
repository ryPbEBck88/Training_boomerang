from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='ar_index'),
    path('ar_bets/', views.ar_bets, name='ar_bets'),
    path('roulette/', views.ar_roulette, name='ar_roulette'),
    path('mix/', views.ar_mix, name='ar_mix'),
    path('mix/continue/', views.ar_mix_continue, name='ar_mix_continue'),
]
