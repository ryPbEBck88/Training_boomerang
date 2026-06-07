"""
Выплата side bet Bonus (Oasis / Caribbean Stud).
Множитель bet-to-1: выплата = bonus_bet * multiplier (чистая выгода сверх ставки).
"""

BONUS_PAYOUT_MULT = {
    "Роял-флеш": 1000,
    "Стрит-флеш": 500,
    "Каре": 200,
    "Фул-хаус": 70,
    "Флеш": 50,
    "Стрит": 40,
    "Сет": 7,
    "Две пары": 2,
}


def get_bonus_payout(bonus_bet, combo):
    """Выплата по бонусу; без комбинации из таблицы — 0."""
    mult = BONUS_PAYOUT_MULT.get(combo, 0)
    return bonus_bet * mult


def check_user_bonus_payout(user_payout, bonus_bet, combo):
    correct = get_bonus_payout(bonus_bet, combo)
    try:
        user_val = float(user_payout)
        if abs(user_val - correct) < 0.01:
            return True, correct
        return False, correct
    except (TypeError, ValueError):
        return False, correct
