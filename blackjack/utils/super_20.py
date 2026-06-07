"""Side bet Super 20 (S): две карты в сумме 20."""

import random

from blackjack.utils.payout import parse_user_amount, round_payout

TEN_RANKS = frozenset({'10', 'J', 'Q', 'K'})
FIRST_RANKS = frozenset({'9', '10', 'J', 'Q', 'K', 'A'})

SUPER20_MULT_MIXED = 3
SUPER20_MULT_SUITED = 7
SUPER20_MULT_PAIR_MIXED = 10
SUPER20_MULT_PAIR_SUITED = 40
SUPER20_MULT_SPADE_QUEENS = 100


def _second_ranks_for_first(first_rank):
    if first_rank == '9':
        return ['A']
    if first_rank == 'A':
        return ['9']
    if first_rank in TEN_RANKS:
        return list(TEN_RANKS)
    return []


def is_super20_hand(card1, card2):
    r1, r2 = card1['rank'], card2['rank']
    if {r1, r2} == {'9', 'A'}:
        return True
    return r1 in TEN_RANKS and r2 in TEN_RANKS


def super_20_payout(bet, card1, card2):
    bet = float(bet or 0)
    if bet <= 0:
        return 0
    if not is_super20_hand(card1, card2):
        return 0

    if (
        card1['rank'] == 'Q'
        and card2['rank'] == 'Q'
        and card1['suit'] == 's'
        and card2['suit'] == 's'
    ):
        return round_payout(bet * SUPER20_MULT_SPADE_QUEENS, bet)

    if card1['rank'] == card2['rank']:
        if card1['suit'] == card2['suit']:
            return round_payout(bet * SUPER20_MULT_PAIR_SUITED, bet)
        return round_payout(bet * SUPER20_MULT_PAIR_MIXED, bet)

    if card1['suit'] == card2['suit']:
        return round_payout(bet * SUPER20_MULT_SUITED, bet)
    return round_payout(bet * SUPER20_MULT_MIXED, bet)


def draw_super20_hand_from_shoe(shoe):
    """Две карты в сумме 20: 9+A или две десятки (10/J/Q/K)."""
    shoe = list(shoe)
    first_cards = [i for i, c in enumerate(shoe) if c['rank'] in FIRST_RANKS]
    random.shuffle(first_cards)
    for i in first_cards:
        c1 = shoe[i]
        for rank2 in _second_ranks_for_first(c1['rank']):
            for j, c2 in enumerate(shoe):
                if j == i or c2['rank'] != rank2:
                    continue
                if not is_super20_hand(c1, c2):
                    continue
                hand = [c1, c2]
                remaining = [c for k, c in enumerate(shoe) if k not in (i, j)]
                return hand, remaining
    raise ValueError('no Super 20 hand available in shoe')


def check_user_super20_payout(user_payout, s_bet, player_hand):
    if len(player_hand) != 2:
        raise ValueError('player_hand must contain 2 cards')
    bet = float(s_bet or 0)
    correct = super_20_payout(bet, player_hand[0], player_hand[1])
    try:
        user_val = parse_user_amount(user_payout)
        if abs(user_val - correct) < 0.02:
            return True, correct
        return False, correct
    except (TypeError, ValueError):
        return False, correct
