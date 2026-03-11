from django.urls import path
from . import views

urlpatterns = [
    path('', views.pvp_index, name='pvp_index'),
    path('create/', views.room_create, name='pvp_room_create'),
    path('find/', views.room_find, name='pvp_room_find'),
    path('room/<str:room_id>/', views.room_detail, name='pvp_room_detail'),
]
