from django.contrib import admin
from .models import Room, RoomPlayer, GameState


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('pk', 'game_type', 'status', 'created_at')
    list_filter = ('game_type', 'status')


@admin.register(RoomPlayer)
class RoomPlayerAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'is_ready', 'joined_at')
    list_filter = ('room',)


@admin.register(GameState)
class GameStateAdmin(admin.ModelAdmin):
    list_display = ('room', 'updated_at')
