"""
URL configuration for training project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView

from .sitemaps import sitemap_view

def favicon_view(request):
    path_ico = settings.BASE_DIR / 'static' / 'images' / 'favicon-48.png'
    with open(path_ico, 'rb') as f:
        r = HttpResponse(f.read(), content_type='image/png')
        r['Cache-Control'] = 'public, max-age=86400'
        return r

def chrome_devtools_json(request):
    return JsonResponse({})  # Chrome DevTools probe — убирает 404 из логов

def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    return HttpResponse(
        f'''User-agent: *
Allow: /
Disallow: /admin/

Sitemap: {sitemap_url}
''',
        content_type='text/plain'
    )

urlpatterns = [
    path('favicon.ico', favicon_view),
    path('robots.txt', robots_txt),
    path('sitemap.xml', sitemap_view),
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools_json),
    path('yandex_70c1c5ce1a91d4b2.html', TemplateView.as_view(template_name='yandex_70c1c5ce1a91d4b2.html', content_type='text/html')),
    path('admin/', admin.site.urls),
    path('', include('homepage.urls')),
    path('staff-room/', include('staffroom.urls')),
    path('blackjack/', include('blackjack.urls')),
    path('poker/', include('poker.urls')),
    path('ar/', include('ar.urls')),
    # Короткий URL: PvP живёт в ar.urls как /ar/pvp/
    path('pvp/', RedirectView.as_view(pattern_name='ar_pvp_lobby', permanent=False, query_string=True)),
]
