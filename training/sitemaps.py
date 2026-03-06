"""
Sitemap для поисковых систем.
"""
import xml.etree.ElementTree as ET
from datetime import datetime

from django.http import HttpResponse
from django.urls import reverse


SITEMAP_URLS = [
    'homepage_index',
    'blackjack_index',
    'blackjack_self_draw',
    'blackjack_payout',
    'poker_index',
    'poker_payout',
    'poker_combo',
    'poker_combo_holdem',
    'poker_texas',
    'ar_index',
    'ar_bets',
    'ar_color_in_cash',
    'ar_payout_through_cash',
    'ar_mix',
]


def sitemap_view(request):
    """Генерирует sitemap.xml на лету (без Sites framework)."""
    urlset = ET.Element(
        'urlset',
        xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'
    )
    base = request.build_absolute_uri('/')[:-1]
    for name in SITEMAP_URLS:
        try:
            path = reverse(name)
        except Exception:
            continue
        loc = base + path
        url_el = ET.SubElement(urlset, 'url')
        ET.SubElement(url_el, 'loc').text = loc
        ET.SubElement(url_el, 'lastmod').text = datetime.utcnow().strftime('%Y-%m-%d')
        ET.SubElement(url_el, 'changefreq').text = 'weekly'
        ET.SubElement(url_el, 'priority').text = '0.8'
    response = HttpResponse(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding='unicode'),
        content_type='application/xml'
    )
    return response
