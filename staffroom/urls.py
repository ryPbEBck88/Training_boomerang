from django.urls import path

from blackjack import views as blackjack_views
from . import views


urlpatterns = [
    path('', views.index, name='staffroom_index'),
    path('blackjack/', blackjack_views.staff_room_blackjack, name='blackjack_staff_room'),
]
