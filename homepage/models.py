from django.conf import settings
from django.db import models


class SitePageVisit(models.Model):
    """Запись просмотра HTML-страницы (учёт посещений)."""

    created_at = models.DateTimeField('время', auto_now_add=True, db_index=True)
    path = models.CharField('путь', max_length=512, db_index=True)
    query_string = models.CharField('query', max_length=512, blank=True)
    status_code = models.PositiveSmallIntegerField('код ответа')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='пользователь',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='site_page_visits',
    )
    session_key = models.CharField('сессия', max_length=40, blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.TextField('User-Agent', blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'просмотр страницы'
        verbose_name_plural = 'просмотры страниц'

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} {self.path}'
