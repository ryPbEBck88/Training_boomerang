from django.test import TestCase

from poker.utils.holdem_compare import best_strength_from_7, comparison_answer, five_card_strength


class HoldemCompareTests(TestCase):
    def _c(self, rank, suit='s'):
        from data.cards import get_deck

        for card in get_deck():
            if card['rank'] == rank and card['suit'] == suit:
                return card
        raise AssertionError(f'card {rank}{suit}')

    def test_guest_stronger_when_dealer_qualifies(self):
        """Дилер в игре (пара четвёрок+), у гостя сильнее — «Старше»."""
        board = [
            self._c('9', 's'),
            self._c('8', 'h'),
            self._c('7', 'd'),
            self._c('6', 'c'),
            self._c('2', 's'),
        ]
        guest = [self._c('K', 'h'), self._c('K', 'd')]
        dealer = [self._c('4', 'c'), self._c('4', 'd')]
        self.assertEqual(comparison_answer(guest, dealer, board), 'older')

    def test_ante_when_dealer_high_card_only(self):
        """У дилера нет игры — только Ante, без сравнения с гостем."""
        board = [
            self._c('K', 's'),
            self._c('9', 'h'),
            self._c('7', 'd'),
            self._c('5', 'c'),
            self._c('2', 's'),
        ]
        guest = [self._c('A', 'c'), self._c('A', 'd')]
        dealer = [self._c('3', 'h'), self._c('4', 'd')]
        self.assertEqual(comparison_answer(guest, dealer, board), 'ante')

    def test_ante_when_dealer_pair_threes(self):
        """Пара троек у дилера — ниже порога пары четвёрок — Ante."""
        board = [
            self._c('K', 's'),
            self._c('Q', 'h'),
            self._c('J', 'd'),
            self._c('10', 'c'),
            self._c('2', 's'),
        ]
        dealer = [self._c('3', 'h'), self._c('3', 'd')]
        guest = [self._c('A', 'c'), self._c('K', 'c')]
        self.assertEqual(comparison_answer(guest, dealer, board), 'ante')

    def test_identical_best_hand_is_stay(self):
        # Лучшая пятёрка целиком с борда (стрит), карманные ниже — у обоих одна сила
        board = [
            self._c('10', 's'),
            self._c('J', 's'),
            self._c('Q', 's'),
            self._c('K', 's'),
            self._c('A', 's'),
        ]
        guest = [self._c('3', 'h'), self._c('4', 'h')]
        dealer = [self._c('5', 'd'), self._c('6', 'd')]
        self.assertEqual(comparison_answer(guest, dealer, board), 'stay')

    def test_wheel_straight_strength(self):
        hand = [
            self._c('A', 'h'),
            self._c('2', 'h'),
            self._c('3', 'h'),
            self._c('4', 'h'),
            self._c('5', 'h'),
        ]
        k = five_card_strength(hand)
        self.assertEqual(k[0], 8)
        self.assertEqual(k[1], 3)

    def test_best_of_seven_picks_nut(self):
        cards = [
            self._c('A', 'h'),
            self._c('K', 'h'),
            self._c('Q', 'h'),
            self._c('J', 'h'),
            self._c('10', 'h'),
            self._c('2', 'c'),
            self._c('3', 'd'),
        ]
        self.assertEqual(best_strength_from_7(cards)[0], 8)


class BonusPayoutTests(TestCase):
    def test_flush_bonus_payout(self):
        from poker.utils.bonus import get_bonus_payout, check_user_bonus_payout

        self.assertEqual(get_bonus_payout(25, 'Флеш'), 1250)
        ok, correct = check_user_bonus_payout('1250', 25, 'Флеш')
        self.assertTrue(ok)
        self.assertEqual(correct, 1250)

    def test_two_pairs_bonus_payout(self):
        from poker.utils.bonus import get_bonus_payout

        self.assertEqual(get_bonus_payout(50, 'Две пары'), 100)

    def test_no_bonus_for_pair(self):
        from poker.utils.bonus import get_bonus_payout

        self.assertEqual(get_bonus_payout(50, 'Пара'), 0)
        self.assertEqual(get_bonus_payout(50, 'Нет игры'), 0)

    def test_bonus_queue_never_contains_pair(self):
        from poker.utils.combo import make_bonus_combo_queue, hand_to_combo, is_bonus_qualifying_combo

        disallowed = {'Пара', 'Туз и король', 'Нет игры'}
        for hand in make_bonus_combo_queue():
            combo = hand_to_combo(hand)
            self.assertNotIn(combo, disallowed)
            self.assertTrue(is_bonus_qualifying_combo(combo))
