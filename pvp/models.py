from django.db import models
from django.conf import settings


class Room(models.Model):
    """PvP room - holds game state and players."""
    GAME_TYPES = [
        ('ar_neighbors', 'AR: Соседи'),
        ('ar_completes', 'AR: Комплиты'),
        ('ar_color_cash', 'AR: Цвет в cash'),
        ('ar_ptc', 'AR: Выплата через cash'),
        ('bj_payout', 'BJ: Выплата'),
        ('bj_self', 'BJ: Набираю себе'),
        ('poker_combo', 'Poker: Комбинации'),
        ('poker_payout', 'Poker: Выплата'),
    ]
    game_type = models.CharField(max_length=32, choices=GAME_TYPES)
    status = models.CharField(
        max_length=16,
        choices=[('waiting', 'Ожидание'), ('active', 'Игра'), ('finished', 'Завершена')],
        default='waiting',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class RoomPlayer(models.Model):
    """Player in a PvP room."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_ready = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['room', 'user']


class GameState(models.Model):
    """Persisted game state for a room (JSON field for flexibility)."""
    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name='game_state')
    state = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)
