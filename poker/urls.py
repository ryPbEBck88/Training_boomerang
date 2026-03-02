from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="poker_index"),
    path('combo/', views.combo, name='poker_combo'),
    path('combo-holdem/', views.combo_holdem, name='poker_combo_holdem'),
    path('texas/', views.texas_holdem, name='poker_texas'),
]
