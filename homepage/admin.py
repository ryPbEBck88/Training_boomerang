from django.contrib import admin

from .models import SitePageVisit


@admin.register(SitePageVisit)
class SitePageVisitAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'path',
        'query_string',
        'status_code',
        'user',
        'ip_address',
    )
    list_filter = ('status_code', 'created_at')
    date_hierarchy = 'created_at'
    search_fields = ('path', 'ip_address', 'user_agent', 'session_key')
    readonly_fields = (
        'created_at',
        'path',
        'query_string',
        'status_code',
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
