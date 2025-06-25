import random

def get_random_bet(min_bet=1, max_bet=100, step=1):
    return random.randrange(min_bet, max_bet + 1, step)

def get_blackjack_payout(bet):
    payout = bet * 1.5
    # Если целое, возвращаем int, если с .5 — оставляем float (для красоты вывода)
    if payout.is_integer():
        return int(payout)
    else:
        return round(payout, 1)

def check_user_payout(user_payout, bet):
    correct = get_blackjack_payout(bet)
    try:
        user_val = float(user_payout)
        # Строгое сравнение: например, 22.5 == 22.5
        return user_val == float(correct), correct
    except Exception:
        return False, correct

