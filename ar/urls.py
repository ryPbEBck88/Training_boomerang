from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='ar_index'),
    path('neighbors/', views.ar_neighbors, name='ar_neighbors'),
    path('completes/', views.ar_completes, name='ar_completes'),
    path('ar_bets/', views.ar_bets, name='ar_bets'),
    path('roulette/', views.ar_roulette, name='ar_roulette'),
    path('color_in_cash/', views.ar_roulette, name='ar_color_in_cash'),
    path('payout_through_cash/', views.ar_payout_through_cash, name='ar_payout_through_cash'),
    path('mix/', views.ar_mix, name='ar_mix'),
    path('mix/to-ptc/', views.ar_mix_to_ptc, name='ar_mix_to_ptc'),
    path('mix/continue/', views.ar_mix_continue, name='ar_mix_continue'),
]
