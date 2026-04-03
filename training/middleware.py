import zoneinfo

from django.conf import settings
from django.utils import timezone


class ActivateTimezoneMiddleware:
    """
    На каждый запрос активирует settings.TIME_ZONE (Москва),
    чтобы даты/время в админке и шаблонах были в одной зоне.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)

    def __call__(self, request):
        timezone.activate(self._tz)
        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()
