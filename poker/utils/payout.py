"""
Таблица выплат Oasis Poker (Caribbean Stud).
Множитель: bet * (multiplier) = payout (чистая выгода сверх ставки).
"""
from .combo import hand_to_combo

# Множители выплат Oasis (bet-to-1): выплата = bet * multiplier
OASIS_PAYOUT_MULT = {
    "Роял-флеш": 201,
    "Стрит-флеш": 101,
    "Каре": 41,
    "Фул-хаус": 15,
    "Флеш": 11,
    "Стрит": 9,
    "Сет": 7,
    "Две пары": 5,
    "Пара": 3,
    "Туз и король": 3,
    "Нет игры": 1,
}


def get_oasis_payout(bet, combo):
    """Выплата (чистая сумма сверх ставки) для комбинации."""
    mult = OASIS_PAYOUT_MULT.get(combo, 1)
    return bet * mult


def check_user_payout(user_payout, bet, combo):
    correct = get_oasis_payout(bet, combo)
    try:
        user_val = float(user_payout)
        if abs(user_val - correct) < 0.01:
            return True, correct
        return False, correct
    except (TypeError, ValueError):
        return False, correct
