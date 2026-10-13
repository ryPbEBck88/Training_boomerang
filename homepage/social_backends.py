"""OAuth backends с .ru-хостами (русскоязычный паспорт Яндекса)."""

from django.conf import settings
from social_core.backends.yandex import YandexOAuth2


class YandexRuOAuth2(YandexOAuth2):
    """Яндекс OAuth через oauth.yandex.ru.

    Redirect URI в кабинете Яндекса часто нельзя изменить и он равен
    корню сайта (без /oauth/complete/...). Подставляем его явно.
    Параметр state у Яндекса часто отсутствует — не требуем его.
    """

    AUTHORIZATION_URL = 'https://oauth.yandex.ru/authorize'
    ACCESS_TOKEN_URL = 'https://oauth.yandex.ru/token'
    REDIRECT_STATE = False
    STATE_PARAMETER = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fixed = (
            self.setting('FIXED_REDIRECT_URI')
            or getattr(settings, 'YANDEX_OAUTH_REDIRECT_URI', '')
            or ''
        ).strip()
        if fixed:
            self.redirect_uri = fixed.rstrip('/')
