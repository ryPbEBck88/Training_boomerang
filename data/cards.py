# data/cards.py

import random

# Масти (suit_code, suit_name_en)
SUITS = [
    ('s', 'spades'),
    ('h', 'hearts'),
    ('d', 'diamonds'),
    ('c', 'clubs'),
]

# Ранги (rank_symbol, value, rank_name_en)
RANKS = [
    ('A', 11, 'ace'),
    ('K', 10, 'king'),
    ('Q', 10, 'queen'),
    ('J', 10, 'jack'),
    ('10', 10, '10'),
    ('9', 9, '9'),
    ('8', 8, '8'),
    ('7', 7, '7'),
    ('6', 6, '6'),
    ('5', 5, '5'),
    ('4', 4, '4'),
    ('3', 3, '3'),
    ('2', 2, '2'),
]

def get_deck():
    """
    Возвращает список из 52 словарей-карт:
    {
        'rank': 'A',
        'suit': 's',
        'name': 'As',
        'value': 11,
        'img': 'ace_of_spades.png'
    }
    """
    deck = []
    for suit_code, suit_name in SUITS:
        for rank, value, rank_en in RANKS:
            img_name = f"{rank_en}_of_{suit_name}.png"
            deck.append({
                'rank': rank,
                'suit': suit_code,
                'name': f"{rank}{suit_code}",
                'value': value,
                'img': img_name
            })
    return deck

def get_shoe(num_decks=1):
    """
    Возвращает 'сапог' (shoe) — несколько колод вместе (по умолчанию одну).
    """
    shoe = []
    for _ in range(num_decks):
        shoe.extend(get_deck())
    return shoe

def shuffle_deck(deck):
    """
    Перемешивает список карт in-place и возвращает его же.
    """
    random.shuffle(deck)
    return deck

def get_shuffled_shoe(num_decks=1):
    """
    Возвращает перемешанный shoe (по умолчанию одна колода).
    """
    shoe = get_shoe(num_decks)
    shuffle_deck(shoe)
    return shoe

def draw_card(deck):
    """
    Вытягивает одну карту из колоды (или shoe).
    Возвращает (card, deck) — карту и оставшуюся колоду.
    """
    card = deck.pop(0) if deck else None
    return card, deck
