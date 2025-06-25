from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='blackjack_index'),
    path('self_draw/', views.self_draw, name='blackjack_self_draw'),
    path('payout/', views.payout_view, name='blackjack_payout'),
]