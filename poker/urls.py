from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="poker_index"),
    path('payout/', views.payout_view, name='poker_payout'),
    path('combo/', views.combo, name='poker_combo'),
    path('combo-holdem/', views.combo_holdem, name='poker_combo_holdem'),
    path('holdem-compare/', views.holdem_comparison, name='poker_holdem_compare'),
    path('texas/', views.texas_holdem, name='poker_texas'),
]
