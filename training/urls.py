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
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.views.generic import TemplateView

from .sitemaps import sitemap_view

def chrome_devtools_json(request):
    return JsonResponse({})  # Chrome DevTools probe — убирает 404 из логов

urlpatterns = [
    path('sitemap.xml', sitemap_view),
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools_json),
    path('yandex_70c1c5ce1a91d4b2.html', TemplateView.as_view(template_name='yandex_70c1c5ce1a91d4b2.html', content_type='text/html')),
    path('admin/', admin.site.urls),
    path('', include('homepage.urls')),
    path('blackjack/', include('blackjack.urls')),
    path('poker/', include('poker.urls')),
    path('ar/', include('ar.urls')),
]
