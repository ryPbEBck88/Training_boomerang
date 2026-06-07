import random

BJ_BONUS_CHIP_VALUES_DESC = [5000, 1000, 500, 100, 25, 5, 2.5, 1]

def _bet_precision(step):
    step = float(step)
    if step == int(step):
        return 0
    text = f'{step:.10f}'.rstrip('0')
    return len(text.split('.')[1]) if '.' in text else 1


def get_random_bet(min_bet, max_bet, step):
    min_bet = float(min_bet)
    max_bet = float(max_bet)
    step = float(step)
    if step <= 0:
        step = 1.0
    n_steps = int(round((max_bet - min_bet) / step))
    k = random.randint(0, n_steps)
    return round(min_bet + k * step, _bet_precision(step))


def amount_representable_as_chips(amount, chip_values_desc=BJ_BONUS_CHIP_VALUES_DESC):
    """Сумма полностью раскладывается на фишки (как на 3D-сукне)."""
    remaining = round(float(amount), 2)
    if remaining < 0:
        return False
    for d in chip_values_desc:
        count = int((remaining + 1e-9) // float(d))
        if count > 0:
            remaining = round(remaining - count * float(d), 2)
    return remaining == 0


def get_random_bonus_bet(min_bet, max_bet, step, chip_values_desc=BJ_BONUS_CHIP_VALUES_DESC):
    """Ставка для BJ Bonus: случайная, но визуально совпадает с суммой фишек."""
    min_bet = float(min_bet)
    max_bet = float(max_bet)
    step = float(step)
    if step <= 0:
        step = 0.5
    n_steps = int(round((max_bet - min_bet) / step))
    if n_steps < 0:
        n_steps = 0
    indices = list(range(n_steps + 1))
    random.shuffle(indices)
    for k in indices:
        bet = round(min_bet + k * step, _bet_precision(step))
        if amount_representable_as_chips(bet, chip_values_desc):
            return bet
    for k in range(n_steps + 1):
        bet = round(min_bet + k * step, _bet_precision(step))
        if amount_representable_as_chips(bet, chip_values_desc):
            return bet
    return round(min_bet, _bet_precision(step))


def parse_user_amount(val):
    """Строка от пользователя → float (пробелы и запятая как в RU-локали)."""
    if val is None:
        raise ValueError('empty amount')
    s = str(val).strip().replace(' ', '').replace(',', '.')
    if not s:
        raise ValueError('empty amount')
    return float(s)


def round_payout(amount, bet):
    prec = _amount_precision(bet)
    payout_prec = _amount_precision(amount)
    prec = max(prec, payout_prec)
    return round(float(amount), prec)


def _amount_precision(value):
    value = float(value)
    if value == int(value):
        return 0
    text = f'{value:.10f}'.rstrip('0')
    return len(text.split('.')[1]) if '.' in text else 0

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
