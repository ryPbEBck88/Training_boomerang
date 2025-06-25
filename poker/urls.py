from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="poker_index"),
    path('combo/', views.combo, name='poker_combo'),
]
