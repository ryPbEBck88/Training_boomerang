import random
from data.cards import get_deck, RANKS as RANK_TUPLES, SUITS as SUIT_TUPLES

RANKS = [r[0] for r in RANK_TUPLES]
SUITS = [s[1] for s in SUIT_TUPLES]
SUIT_NAME_TO_CODE = dict(SUIT_TUPLES)

COMBO_CHOICES = [
    "Нет игры", "Туз и король", "Пара", "Две пары", "Сет",
    "Стрит", "Флеш", "Фул-хаус", "Каре", "Стрит-флеш", "Роял-флеш"
]

def get_hand_no_combo():
    while True:
        hand = random.sample(get_deck(), 5)
        ranks = set(card['rank'] for card in hand)
        suits = set(card['suit'] for card in hand)
        if len(ranks) == 5 and len(suits) > 1:
            rv = [RANKS.index(card['rank']) for card in hand]
            rv.sort()
            if rv != list(range(rv[0], rv[0]+5)):
                if not ('A' in ranks and 'K' in ranks):
                    return hand

def get_hand_ace_king():
    while True:
        hand = random.sample(get_deck(), 5)
        ranks = [card['rank'] for card in hand]
        if 'A' in ranks and 'K' in ranks and len(set(ranks)) == 5:
            if ranks.count('A') == 1 and ranks.count('K') == 1:
                return hand

def get_hand_pair():
    while True:
        deck = get_deck()
        pair_rank = random.choice(RANKS)
        pair_cards = random.sample([c for c in deck if c['rank'] == pair_rank], 2)
        other_ranks = [r for r in RANKS if r != pair_rank]
        others = []
        while len(others) < 3:
            r = random.choice(other_ranks)
            c = random.choice([card for card in deck if card['rank'] == r])
            if c not in pair_cards and all(o['rank'] != r for o in others):
                others.append(c)
        hand = pair_cards + others
        rv = [RANKS.index(card['rank']) for card in hand]
        rv.sort()
        if rv != list(range(rv[0], rv[0]+5)) and not ('A' in [c['rank'] for c in hand] and 'K' in [c['rank'] for c in hand]):
            return hand

def get_hand_two_pairs():
    while True:
        deck = get_deck()
        pair_ranks = random.sample(RANKS, 2)
        pair1 = random.sample([c for c in deck if c['rank'] == pair_ranks[0]], 2)
        pair2 = random.sample([c for c in deck if c['rank'] == pair_ranks[1]], 2)
        left_ranks = [r for r in RANKS if r not in pair_ranks]
        kicker = random.choice([c for c in deck if c['rank'] in left_ranks])
        hand = pair1 + pair2 + [kicker]
        rv = [RANKS.index(card['rank']) for card in hand]
        rv.sort()
        if rv != list(range(rv[0], rv[0]+5)):
            return hand

def get_hand_set():
    while True:
        deck = get_deck()
        set_rank = random.choice(RANKS)
        set_cards = random.sample([c for c in deck if c['rank'] == set_rank], 3)
        other_ranks = [r for r in RANKS if r != set_rank]
        others = []
        while len(others) < 2:
            r = random.choice(other_ranks)
            c = random.choice([card for card in deck if card['rank'] == r])
            if c not in set_cards and all(o['rank'] != r for o in others):
                others.append(c)
        hand = set_cards + others
        rank_counts = {r:0 for r in RANKS}
        for c in hand:
            rank_counts[c['rank']] += 1
        if list(rank_counts.values()).count(2) == 0:
            return hand

def get_hand_straight():
    while True:
        start = random.randint(0, 8)
        ranks = RANKS[start:start+5]
        deck = get_deck()
        hand = []
        used = set()
        for r in ranks:
            cards = [c for c in deck if c['rank'] == r and c['img'] not in used]
            if not cards:
                break
            card = random.choice(cards)
            hand.append(card)
            used.add(card['img'])
        if len(hand) == 5:
            return hand

def get_hand_flush():
    while True:
        suit_code = random.choice(list(SUIT_NAME_TO_CODE.keys()))
        deck = [c for c in get_deck() if c['suit'] == suit_code]
        cards = random.sample(deck, 5)
        rv = [RANKS.index(card['rank']) for card in cards]
        rv.sort()
        if rv != list(range(rv[0], rv[0]+5)):
            return cards

def get_hand_full_house():
    deck = get_deck()
    ranks = random.sample(RANKS, 2)
    trio = random.sample([c for c in deck if c['rank'] == ranks[0]], 3)
    pair = random.sample([c for c in deck if c['rank'] == ranks[1]], 2)
    return trio + pair

def get_hand_quads():
    deck = get_deck()
    rank = random.choice(RANKS)
    quads = random.sample([c for c in deck if c['rank'] == rank], 4)
    left_ranks = [r for r in RANKS if r != rank]
    kicker = random.choice([c for c in deck if c['rank'] in left_ranks])
    return quads + [kicker]

def get_hand_straight_flush():
    while True:
        suit_code = random.choice(list(SUIT_NAME_TO_CODE.keys()))
        start = random.randint(0, 7)
        ranks = RANKS[start:start+5]
        if set(ranks) == set(['10', 'J', 'Q', 'K', 'A']):
            continue
        deck = [c for c in get_deck() if c['rank'] in ranks and c['suit'] == suit_code]
        if len(deck) >= 5:
            return random.sample(deck, 5)

def get_hand_royal_flush():
    suit_code = random.choice(list(SUIT_NAME_TO_CODE.keys()))
    ranks = ['10', 'J', 'Q', 'K', 'A']
    deck = [c for c in get_deck() if c['rank'] in ranks and c['suit'] == suit_code]
    if len(deck) >= 5:
        return random.sample(deck, 5)

def hand_to_combo(hand):
    ranks = [card['rank'] for card in hand]
    suits = [card['suit'] for card in hand]
    rank_counts = {r: ranks.count(r) for r in set(ranks)}
    values = sorted([RANKS.index(r) for r in ranks])
    is_flush = len(set(suits)) == 1
    is_straight = values == list(range(values[0], values[0] + 5))
    if set(ranks) == set(['A', '2', '3', '4', '5']):
        is_straight = True

    if is_flush and set(ranks) == set(['10', 'J', 'Q', 'K', 'A']):
        return "Роял-флеш"
    if is_flush and is_straight:
        return "Стрит-флеш"
    if 4 in rank_counts.values():
        return "Каре"
    if sorted(rank_counts.values()) == [2, 3]:
        return "Фул-хаус"
    if is_flush:
        return "Флеш"
    if is_straight:
        return "Стрит"
    if 3 in rank_counts.values():
        return "Сет"
    if list(rank_counts.values()).count(2) == 2:
        return "Две пары"
    if 2 in rank_counts.values():
        return "Пара"
    if 'A' in ranks and 'K' in ranks and len(set(ranks)) == 5:
        return "Туз и король"
    return "Нет игры"

def make_combo_queue():
    queue = []
    queue += [get_hand_no_combo() for _ in range(1)]
    queue += [get_hand_ace_king() for _ in range(2)]
    queue += [get_hand_pair() for _ in range(2)]
    queue += [get_hand_two_pairs() for _ in range(2)]
    queue += [get_hand_set() for _ in range(2)]
    queue += [get_hand_straight() for _ in range(3)]
    queue += [get_hand_flush() for _ in range(3)]
    queue += [get_hand_full_house() for _ in range(3)]
    queue += [get_hand_quads() for _ in range(2)]
    queue += [get_hand_straight_flush() for _ in range(1)]
    queue += [get_hand_royal_flush() for _ in range(1)]
    random.shuffle(queue)
    return queue