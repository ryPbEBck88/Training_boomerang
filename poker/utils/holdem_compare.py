"""
Полное сравнение лучшей 5-карточной руки из 7 (Texas Hold'em), с кикерами.
Для тренажёра «старше / младше / ничья» гость против дилера.
"""
from itertools import combinations

# 2 — низший, A — старший (стандартный покер ace-high)
RANK_ORDER = {
    '2': 0,
    '3': 1,
    '4': 2,
    '5': 3,
    '6': 4,
    '7': 5,
    '8': 6,
    '9': 7,
    '10': 8,
    'J': 9,
    'Q': 10,
    'K': 11,
    'A': 12,
}


def _rank_values(hand):
    return [RANK_ORDER[c['rank']] for c in hand]


def _straight_high_card(rank_values):
    uniq = sorted(set(rank_values))
    if len(uniq) != 5:
        return None
    # Колесо A-2-3-4-5: старшая карта стрита — пятёрка
    if uniq == [0, 1, 2, 3, 12]:
        return 3
    if uniq[-1] - uniq[0] == 4:
        return uniq[-1]
    return None


def five_card_strength(hand):
    """
    Кортеж для сравнения: больше = сильнее. Стандартные правила Hold'em
    (пара двоек сильнее старшей карты и т.д.).
    """
    ranks = [c['rank'] for c in hand]
    suits = [c['suit'] for c in hand]
    vals = _rank_values(hand)
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1

    is_flush = len(set(suits)) == 1
    str_hi = _straight_high_card(vals)
    is_straight = str_hi is not None

    if is_flush and is_straight:
        return (8, str_hi)
    if 4 in counts.values():
        quad = next(v for v, n in counts.items() if n == 4)
        kicker = next(v for v, n in counts.items() if n == 1)
        return (7, quad, kicker)
    if sorted(counts.values()) == [2, 3]:
        trip = next(v for v, n in counts.items() if n == 3)
        pair = next(v for v, n in counts.items() if n == 2)
        return (6, trip, pair)
    if is_flush:
        return (5,) + tuple(sorted(vals, reverse=True))
    if is_straight:
        return (4, str_hi)
    if 3 in counts.values():
        trip = next(v for v, n in counts.items() if n == 3)
        kickers = sorted([v for v, n in counts.items() if n == 1], reverse=True)
        return (3, trip) + tuple(kickers)
    if list(counts.values()).count(2) == 2:
        pairs = sorted([v for v, n in counts.items() if n == 2], reverse=True)
        kicker = next(v for v, n in counts.items() if n == 1)
        return (2, pairs[0], pairs[1], kicker)
    if 2 in counts.values():
        pair = next(v for v, n in counts.items() if n == 2)
        kickers = sorted([v for v, n in counts.items() if n == 1], reverse=True)
        return (1, pair) + tuple(kickers)
    return (0,) + tuple(sorted(vals, reverse=True))


def best_strength_from_7(cards):
    best = None
    for five in combinations(cards, 5):
        k = five_card_strength(list(five))
        if best is None or k > best:
            best = k
    return best


# Минимальный ранг пары для «игры» дилера (пара четвёрок и старше)
DEALER_MIN_PAIR_RANK = RANK_ORDER['4']


def dealer_qualifies_pair_fours(dealer_hole, board):
    """
    Дилер «в игре», если лучшая 5 из 7 — не слабее пары четвёрок
    (старшая карта, пара 2–3 — нет игры).
    """
    s = best_strength_from_7(list(dealer_hole) + list(board))
    cat = s[0]
    if cat >= 2:
        return True
    if cat == 1:
        pair_rank = s[1]
        return pair_rank >= DEALER_MIN_PAIR_RANK
    return False


def comparison_answer(guest_hole, dealer_hole, board):
    """
    Правильный выбор в тренажёре.
    Если у дилера нет игры — только 'ante'.
    Иначе: 'older' / 'younger' / 'stay' по сравнению с гостем.
    """
    if not dealer_qualifies_pair_fours(dealer_hole, board):
        return 'ante'
    g = best_strength_from_7(list(guest_hole) + list(board))
    d = best_strength_from_7(list(dealer_hole) + list(board))
    if g > d:
        return 'older'
    if g < d:
        return 'younger'
    return 'stay'
