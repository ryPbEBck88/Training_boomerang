from django.contrib import admin
from .models import ArPvpPlayer, ArPvpRoom, ArTrainingAttempt


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


@admin.register(ArTrainingAttempt)
class ArTrainingAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "trainer_slug", "outcome", "solve_seconds", "created_at")
    search_fields = ("user__username", "trainer_slug")
    list_filter = ("trainer_slug", "outcome")
