from django.conf import settings


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()[:45]
    return (request.META.get('REMOTE_ADDR') or '')[:45] or None


def _should_skip_path(path):
    if not path or not path.startswith('/'):
        return True
    lower = path.lower()
    prefixes = (
        '/static/',
        '/media/',
        '/admin/',
    )
    if any(lower.startswith(p) for p in prefixes):
        return True
    exact = {
        '/favicon.ico',
        '/robots.txt',
        '/sitemap.xml',
    }
    if lower in exact:
        return True
    if lower.startswith('/.well-known/'):
        return True
    static_ext = ('.js', '.css', '.map', '.ico', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.woff', '.woff2')
    if any(lower.endswith(ext) for ext in static_ext):
        return True
    return False


class SiteVisitLogMiddleware:
    """
    Пишет в БД успешные GET-запросы с ответом text/html (просмотр страниц).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._maybe_log(request, response)
        except Exception:
            # Не ломаем ответ из-за аналитики
            if settings.DEBUG:
                raise
        return response

    def _maybe_log(self, request, response):
        if not getattr(settings, 'SITE_VISIT_LOG_ENABLED', True):
            return
        if request.method != 'GET':
            return
        if response.status_code >= 400:
            return
        ct = (response.get('Content-Type') or '').split(';')[0].strip().lower()
        if ct != 'text/html':
            return
        path = request.path or '/'
        if _should_skip_path(path):
            return
        if getattr(response, 'streaming_content', None) is not None:
            return

        from homepage.models import SitePageVisit

        qs = (request.META.get('QUERY_STRING') or '')[:512]
        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
        sk = ''
        if hasattr(request, 'session') and request.session.session_key:
            sk = request.session.session_key[:40]

        ua = (request.META.get('HTTP_USER_AGENT') or '')[:2000]
        ip_raw = _client_ip(request)
        ip = ip_raw
        if ip_raw:
            try:
                from ipaddress import ip_address

                ip_address(ip_raw)
            except ValueError:
                ip = None

        SitePageVisit.objects.create(
            path=path[:512],
            query_string=qs,
            status_code=response.status_code,
            user=user,
            session_key=sk,
            ip_address=ip,
            user_agent=ua,
        )
