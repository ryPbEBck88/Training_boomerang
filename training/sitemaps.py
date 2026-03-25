"""
Sitemap для поисковых систем.
"""
import xml.etree.ElementTree as ET
from datetime import datetime

from django.http import HttpResponse
from django.urls import reverse


# (url_name, priority) — главная 1.0, разделы 0.9, остальное 0.8
SITEMAP_URLS = [
    ('homepage_index', '1.0'),
    ('blackjack_index', '0.9'),
    ('blackjack_self_draw', '0.8'),
    ('blackjack_payout', '0.8'),
    ('poker_index', '0.9'),
    ('poker_payout', '0.8'),
    ('poker_combo', '0.8'),
    ('poker_combo_holdem', '0.8'),
    ('poker_texas', '0.8'),
    ('ar_index', '0.9'),
    ('ar_bets', '0.8'),
    ('ar_neighbors', '0.8'),
    ('ar_completes', '0.8'),
    ('ar_color_in_cash', '0.8'),
    ('ar_payout_through_cash', '0.8'),
    ('ar_mix', '0.8'),
    ('ar_bet_reveal', '0.8'),
]


def sitemap_view(request):
    """Генерирует sitemap.xml на лету (без Sites framework)."""
    urlset = ET.Element(
        'urlset',
        xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'
    )
    base = request.build_absolute_uri('/')[:-1]
    for item in SITEMAP_URLS:
        name = item[0] if isinstance(item, (list, tuple)) else item
        priority = item[1] if isinstance(item, (list, tuple)) and len(item) > 1 else '0.8'
        try:
            path = reverse(name)
        except Exception:
            continue
        loc = base + path
        url_el = ET.SubElement(urlset, 'url')
        ET.SubElement(url_el, 'loc').text = loc
        ET.SubElement(url_el, 'lastmod').text = datetime.utcnow().strftime('%Y-%m-%d')
        ET.SubElement(url_el, 'changefreq').text = 'weekly'
        ET.SubElement(url_el, 'priority').text = priority
    response = HttpResponse(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding='unicode'),
        content_type='application/xml'
    )
    return response
