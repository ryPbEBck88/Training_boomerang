from django.test import SimpleTestCase

from blackjack.utils.bonus_side_bets import (
    check_user_side_bets_payout,
    combo_from_three,
    get_total_side_bets_payout,
    match_dealer_payout,
    perfect_pairs_payout,
    side_21_3_payout,
)
from blackjack.utils.super_20 import (
    check_user_super20_payout,
    draw_super20_hand_from_shoe,
    is_super20_hand,
    super_20_payout,
)


def _card(rank, suit='s'):
    return {'rank': rank, 'suit': suit, 'img': f'{rank}{suit}.png', 'name': f'{rank}{suit}'}


class BonusSideBetsTests(SimpleTestCase):
    def test_perfect_pair_mixed(self):
        self.assertEqual(perfect_pairs_payout(10, _card('K', 's'), _card('K', 'h')), 50)

    def test_perfect_pair_colored(self):
        self.assertEqual(perfect_pairs_payout(10, _card('7', 'h'), _card('7', 'd')), 100)

    def test_perfect_pair_perfect(self):
        self.assertEqual(perfect_pairs_payout(10, _card('A', 's'), _card('A', 's')), 300)

    def test_draw_pair_hand_from_shoe(self):
        from data.cards import get_shuffled_shoe
        from blackjack.utils.bonus_side_bets import draw_pair_hand_from_shoe

        for _ in range(50):
            shoe = get_shuffled_shoe(num_decks=6)
            hand, _ = draw_pair_hand_from_shoe(shoe)
            self.assertEqual(len(hand), 2)
            self.assertEqual(hand[0]['rank'], hand[1]['rank'])

    def test_21_3_flush(self):
        hand = [_card('2', 'h'), _card('5', 'h')]
        dealer = _card('9', 'h')
        self.assertEqual(combo_from_three(hand + [dealer]), 'Флеш')
        self.assertEqual(side_21_3_payout(10, hand, dealer), 50)

    def test_21_3_straight(self):
        hand = [_card('4', 's'), _card('5', 'h')]
        dealer = _card('6', 'd')
        self.assertEqual(combo_from_three(hand + [dealer]), 'Стрит')
        self.assertEqual(side_21_3_payout(10, hand, dealer), 100)

    def test_match_dealer_one(self):
        hand = [_card('K', 's'), _card('7', 'h')]
        dealer = _card('K', 'd')
        self.assertEqual(match_dealer_payout(10, hand, dealer), 40)

    def test_match_dealer_two(self):
        hand = [_card('Q', 's'), _card('Q', 'h')]
        dealer = _card('Q', 'd')
        self.assertEqual(match_dealer_payout(10, hand, dealer), 80)

    def test_total_and_check(self):
        hand = [_card('8', 'h'), _card('8', 'd')]
        dealer = _card('8', 's')
        pp, s, d = 10, 0, 10
        total = get_total_side_bets_payout(pp, s, d, hand, dealer)
        self.assertEqual(total, 100 + 80)
        ok, correct = check_user_side_bets_payout('180', pp, s, d, hand, dealer)
        self.assertTrue(ok)
        self.assertEqual(correct, 180)

    def test_zero_bets(self):
        hand = [_card('2', 's'), _card('3', 'h')]
        dealer = _card('K', 'd')
        self.assertEqual(get_total_side_bets_payout(0, 0, 0, hand, dealer), 0)


class Super20Tests(SimpleTestCase):
    def test_nine_ace_mixed(self):
        self.assertEqual(super_20_payout(10, _card('9', 'h'), _card('A', 's')), 30)

    def test_nine_ace_suited(self):
        self.assertEqual(super_20_payout(10, _card('9', 'd'), _card('A', 'd')), 70)

    def test_tens_pair_mixed(self):
        self.assertEqual(super_20_payout(10, _card('K', 's'), _card('K', 'h')), 100)

    def test_tens_pair_suited(self):
        self.assertEqual(super_20_payout(10, _card('10', 'c'), _card('10', 'c')), 400)

    def test_spade_queens(self):
        self.assertEqual(super_20_payout(10, _card('Q', 's'), _card('Q', 's')), 1000)

    def test_jack_queen_no_pair_mixed(self):
        self.assertEqual(super_20_payout(10, _card('J', 'h'), _card('Q', 's')), 30)

    def test_draw_super20_hand(self):
        from data.cards import get_shuffled_shoe
        from blackjack.utils.super_20 import draw_super20_hand_from_shoe, is_super20_hand

        for _ in range(50):
            shoe = get_shuffled_shoe(num_decks=6)
            hand, _ = draw_super20_hand_from_shoe(shoe)
            self.assertEqual(len(hand), 2)
            self.assertTrue(is_super20_hand(hand[0], hand[1]))

    def test_check_user(self):
        hand = [_card('9', 'h'), _card('A', 'd')]
        ok, correct = check_user_super20_payout('30', 10, hand)
        self.assertTrue(ok)
        self.assertEqual(correct, 30)

    def test_check_user_comma_and_fractional_bet(self):
        hand = [_card('9', 'h'), _card('A', 's')]
        ok, correct = check_user_super20_payout('385,5', 128.5, hand)
        self.assertTrue(ok)
        self.assertEqual(correct, 385.5)


class BonusBetChipTests(SimpleTestCase):
    def test_129_not_representable_as_chips(self):
        from blackjack.utils.payout import amount_representable_as_chips

        self.assertFalse(amount_representable_as_chips(129))

    def test_128_5_representable(self):
        from blackjack.utils.payout import amount_representable_as_chips

        self.assertTrue(amount_representable_as_chips(128.5))

    def test_random_bonus_bet_always_representable(self):
        from blackjack.utils.payout import amount_representable_as_chips, get_random_bonus_bet

        for _ in range(200):
            bet = get_random_bonus_bet(1, 200, 0.5)
            self.assertTrue(amount_representable_as_chips(bet), bet)
