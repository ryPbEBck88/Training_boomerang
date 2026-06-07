"""Side bets P (Perfect Pairs), S (21+3), D (Match the Dealer)."""

import random

from poker.utils.combo import RANKS

RED_SUITS = frozenset({'h', 'd'})

PERFECT_PAIRS_MULT_MIXED = 5
PERFECT_PAIRS_MULT_COLORED = 10
PERFECT_PAIRS_MULT_SUIT = 30

# 21+3: выплата = bet × multiplier (чистая прибыль)
SIDE_21_3_MULT = {
    'Флеш': 5,
    'Стрит': 10,
    'Сет': 30,
    'Стрит-флеш': 40,
}


def _rank_index(rank):
    return RANKS.index(rank) if rank in RANKS else -1


def combo_from_three(cards):
    """Лучшая 3-карточная комбинация для 21+3."""
    if len(cards) != 3:
        raise ValueError('21+3 requires exactly 3 cards')
    ranks = [c['rank'] for c in cards]
    suits = [c['suit'] for c in cards]
    rank_counts = {r: ranks.count(r) for r in set(ranks)}
    values = sorted(_rank_index(r) for r in ranks)
    is_flush = len(set(suits)) == 1
    is_straight = (
        len(set(ranks)) == 3
        and values == list(range(values[0], values[0] + 3))
    )
    if set(ranks) == {'A', '2', '3'}:
        is_straight = True

    if is_flush and is_straight:
        return 'Стрит-флеш'
    if 3 in rank_counts.values():
        return 'Сет'
    if is_flush:
        return 'Флеш'
    if is_straight:
        return 'Стрит'
    return None


def perfect_pairs_payout(bet, card1, card2):
    if bet <= 0:
        return 0
    if card1['rank'] != card2['rank']:
        return 0
    if card1['suit'] == card2['suit']:
        return bet * PERFECT_PAIRS_MULT_SUIT
    if (card1['suit'] in RED_SUITS) == (card2['suit'] in RED_SUITS):
        return bet * PERFECT_PAIRS_MULT_COLORED
    return bet * PERFECT_PAIRS_MULT_MIXED


def draw_pair_hand_from_shoe(shoe):
    """Две карты одного ранга из shoe (2…2, …, A…A)."""
    by_rank = {}
    for card in shoe:
        by_rank.setdefault(card['rank'], []).append(card)
    eligible = [rank for rank, cards in by_rank.items() if len(cards) >= 2]
    if not eligible:
        raise ValueError('no pair available in shoe')
    rank = random.choice(eligible)
    pair = random.sample(by_rank[rank], 2)
    for card in pair:
        shoe.remove(card)
    return pair, shoe


def side_21_3_payout(bet, player_hand, dealer_up):
    if bet <= 0:
        return 0
    combo = combo_from_three(list(player_hand) + [dealer_up])
    if not combo:
        return 0
    return bet * SIDE_21_3_MULT.get(combo, 0)


def match_dealer_payout(bet, player_hand, dealer_up):
    if bet <= 0:
        return 0
    rank = dealer_up['rank']
    matches = sum(1 for c in player_hand if c['rank'] == rank)
    if matches >= 2:
        return bet * 8
    if matches == 1:
        return bet * 4
    return 0


def get_total_side_bets_payout(pp_bet, s_bet, d_bet, player_hand, dealer_up):
    if len(player_hand) != 2:
        raise ValueError('player_hand must contain 2 cards')
    total = 0
    total += perfect_pairs_payout(pp_bet, player_hand[0], player_hand[1])
    total += side_21_3_payout(s_bet, player_hand, dealer_up)
    total += match_dealer_payout(d_bet, player_hand, dealer_up)
    return total


def check_user_side_bets_payout(user_payout, pp_bet, s_bet, d_bet, player_hand, dealer_up):
    correct = get_total_side_bets_payout(pp_bet, s_bet, d_bet, player_hand, dealer_up)
    try:
        user_val = float(user_payout)
        if abs(user_val - correct) < 0.01:
            return True, correct
        return False, correct
    except (TypeError, ValueError):
        return False, correct
