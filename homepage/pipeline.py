"""Pipeline для social-auth: соц.вход активирует пользователя и связывает по email."""

from django.contrib.auth import get_user_model

User = get_user_model()


def activate_social_user(backend, user=None, *args, **kwargs):
    if user is None:
        return
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=['is_active'])


def associate_by_email(backend, details, user=None, *args, **kwargs):
    """Если email уже есть в системе — привязать соц.аккаунт к нему."""
    if user:
        return {'user': user}
    email = (details.get('email') or '').strip().lower()
    if not email:
        return
    existing = User.objects.filter(email__iexact=email).order_by('id').first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.save(update_fields=['is_active'])
        return {'user': existing, 'is_new': False}
