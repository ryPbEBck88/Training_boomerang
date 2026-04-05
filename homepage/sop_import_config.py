"""Источники импорта тестов СОП из Excel (static/boomerang/sop/)."""

from pathlib import Path

from django.conf import settings

SOP_XLSX_DIR = Path(settings.BASE_DIR) / 'static' / 'boomerang' / 'sop'

# Колонки: № | Вопрос | Правильный ответ | Неверный ответ 1–3
SOP_IMPORT_SOURCES = [
    {
        'file': 'Black Jack (1).xlsx',
        'sheets': [
            {'sheet': 'Блэк Джек', 'slug': 'sop-blackjack', 'title': 'СОП: Блэк-джек'},
            {'sheet': 'Poker', 'slug': 'sop-poker', 'title': 'СОП: Покер'},
        ],
    },
    {
        'file': 'Novopoker.xlsx',
        'sheets': [
            {'sheet': 0, 'slug': 'sop-novopoker', 'title': 'СОП: Novopoker'},
        ],
    },
    {
        'file': 'Oazis Poker.xlsx',
        'sheets': [
            {'sheet': 0, 'slug': 'sop-oazis-poker', 'title': 'СОП: Оазис покер'},
        ],
    },
]
