from django.contrib import admin
from .models import ArPvpPlayer, ArPvpRoom


@admin.register(ArPvpRoom)
class ArPvpRoomAdmin(admin.ModelAdmin):
    list_display = ("code", "game_slug", "status", "max_players", "target_score", "round_number", "created_at")
    search_fields = ("code",)
    list_filter = ("status", "game_slug", "max_players")


@admin.register(ArPvpPlayer)
class ArPvpPlayerAdmin(admin.ModelAdmin):
    list_display = ("display_name", "room", "seat_no", "score", "is_ready", "answered_round", "joined_at")
    search_fields = ("display_name", "room__code")
    list_filter = ("is_ready",)
