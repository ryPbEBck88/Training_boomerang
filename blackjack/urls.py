from django.urls import path
from django.views.generic import RedirectView
from . import views


urlpatterns = [
    path('', views.index, name='blackjack_index'),
    path('staff-room/', RedirectView.as_view(pattern_name='blackjack_staff_room', permanent=False), name='blackjack_staff_room_legacy'),
    path('self_draw/', views.self_draw, name='blackjack_self_draw'),
    path('payout/', views.payout_view, name='blackjack_payout'),
]