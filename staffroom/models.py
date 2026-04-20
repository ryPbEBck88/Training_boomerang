from decimal import Decimal

from django.conf import settings
from django.db import models


class StaffWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_wallet',
        verbose_name='пользователь',
    )
    balance = models.DecimalField(
        'баланс',
        max_digits=12,
        decimal_places=2,
        default=Decimal('1000.00'),
    )
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('обновлён', auto_now=True)

    class Meta:
        verbose_name = 'кошелёк staff room'
        verbose_name_plural = 'кошельки staff room'

    def __str__(self):
        return f'{self.user}: {self.balance}'
