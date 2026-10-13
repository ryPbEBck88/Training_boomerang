from django.conf import settings


def auth_social(request):
    vk = bool(
        getattr(settings, 'SOCIAL_AUTH_VK_OAUTH2_KEY', '')
        and getattr(settings, 'SOCIAL_AUTH_VK_OAUTH2_SECRET', '')
    )
    yandex = bool(
        getattr(settings, 'SOCIAL_AUTH_YANDEX_OAUTH2_KEY', '')
        and getattr(settings, 'SOCIAL_AUTH_YANDEX_OAUTH2_SECRET', '')
    )
    return {
        'vk_oauth_enabled': vk,
        'yandex_oauth_enabled': yandex,
        'social_oauth_any': vk or yandex,
    }
