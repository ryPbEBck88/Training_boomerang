from django.contrib import admin

from .models import SitePageVisit, SopAnswer, SopGameTest, SopQuestion


@admin.register(SitePageVisit)
class SitePageVisitAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'http_method',
        'path',
        'status_code',
        'content_type',
        'query_string',
        'user',
        'ip_address',
    )
    list_filter = ('http_method', 'status_code', 'created_at')
    date_hierarchy = 'created_at'
    search_fields = ('path', 'ip_address', 'user_agent', 'session_key', 'content_type')
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at',
        'http_method',
        'path',
        'query_string',
        'status_code',
        'content_type',
        'user',
        'session_key',
        'ip_address',
        'user_agent',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class SopAnswerInline(admin.TabularInline):
    model = SopAnswer
    extra = 0


@admin.register(SopGameTest)
class SopGameTestAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'question_count', 'updated_at')
    search_fields = ('slug', 'title')

    @admin.display(description='вопросов')
    def question_count(self, obj):
        return obj.questions.count()


@admin.register(SopQuestion)
class SopQuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'test', 'sort_order')
    list_filter = ('test',)
    search_fields = ('text',)
    inlines = [SopAnswerInline]
    ordering = ('test', 'sort_order', 'id')

    @admin.display(description='вопрос')
    def short_text(self, obj):
        t = obj.text
        return (t[:70] + '…') if len(t) > 70 else t
