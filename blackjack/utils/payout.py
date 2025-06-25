import random

def get_random_bet(min_bet, max_bet, step):
    return random.randrange(min_bet, max_bet + 1, step)

def get_blackjack_payout(bet):
    return round(bet * 1.5, 1)

def check_user_payout(user_payout, bet):
    correct = get_blackjack_payout(bet)
    try:
        user_val = float(user_payout)
        if abs(user_val - correct) < 0.01:
            return True, correct
        else:
            return False, correct
    except Exception:
        return False, correct
