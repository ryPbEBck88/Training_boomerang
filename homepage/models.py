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


class SopGameTest(models.Model):
    """Тест СОП по одной игре (набор вопросов)."""

    slug = models.SlugField('код URL', max_length=80, unique=True, db_index=True)
    title = models.CharField('название', max_length=200)
    description = models.TextField('описание', blank=True)
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('обновлён', auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'тест СОП'
        verbose_name_plural = 'тесты СОП'

    def __str__(self):
        return self.title


class SopQuestion(models.Model):
    test = models.ForeignKey(
        SopGameTest,
        verbose_name='тест',
        related_name='questions',
        on_delete=models.CASCADE,
    )
    text = models.TextField('вопрос')
    sort_order = models.PositiveIntegerField('порядок', default=0)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'вопрос СОП'
        verbose_name_plural = 'вопросы СОП'

    def __str__(self):
        return (self.text[:60] + '…') if len(self.text) > 60 else self.text


class SopAnswer(models.Model):
    question = models.ForeignKey(
        SopQuestion,
        verbose_name='вопрос',
        related_name='answers',
        on_delete=models.CASCADE,
    )
    text = models.TextField('текст ответа')
    is_correct = models.BooleanField('верный', default=False)

    class Meta:
        ordering = ['id']
        verbose_name = 'вариант ответа'
        verbose_name_plural = 'варианты ответа'

    def __str__(self):
        mark = '✓ ' if self.is_correct else ''
        return f'{mark}{self.text[:40]}'
