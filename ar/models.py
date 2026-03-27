from django.db import models


class ArPvpRoom(models.Model):
    STATUS_LOBBY = "lobby"
    STATUS_IN_ROUND = "in_round"
    STATUS_ROUND_RESULT = "round_result"
    STATUS_FINISHED = "finished"
    STATUS_CHOICES = (
        (STATUS_LOBBY, "Lobby"),
        (STATUS_IN_ROUND, "In round"),
        (STATUS_ROUND_RESULT, "Round result"),
        (STATUS_FINISHED, "Finished"),
    )

    code = models.CharField(max_length=8, unique=True, db_index=True)
    game_slug = models.CharField(max_length=64, default="ar_bets")
    max_players = models.PositiveSmallIntegerField(default=2)
    host_session_key = models.CharField(max_length=128)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_LOBBY)
    target_score = models.PositiveSmallIntegerField(default=5)
    timer_enabled = models.BooleanField(default=True)
    timer_seconds = models.PositiveSmallIntegerField(default=20)
    use_stacks = models.BooleanField(default=True)
    stacks_count = models.PositiveSmallIntegerField(default=1)
    min_chips = models.PositiveSmallIntegerField(default=0)
    max_chips = models.PositiveSmallIntegerField(default=5)
    round_number = models.PositiveIntegerField(default=0)
    round_payload = models.JSONField(default=dict, blank=True)
    round_started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} ({self.game_slug})"


class ArPvpPlayer(models.Model):
    room = models.ForeignKey(ArPvpRoom, on_delete=models.CASCADE, related_name="players")
    session_key = models.CharField(max_length=128)
    display_name = models.CharField(max_length=64, default="Игрок")
    seat_no = models.PositiveSmallIntegerField(default=1)
    score = models.PositiveIntegerField(default=0)
    is_ready = models.BooleanField(default=False)
    answered_round = models.PositiveIntegerField(default=0)
    last_answer_correct = models.BooleanField(default=False)
    last_answer_ms = models.PositiveIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("room", "session_key"),)
        ordering = ("seat_no", "joined_at")

    def __str__(self):
        return f"{self.display_name} @ {self.room.code}"
