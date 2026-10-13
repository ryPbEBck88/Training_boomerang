from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """Вход по имени пользователя или по email (без учёта регистра)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or password is None:
            return None
        login = str(username).strip()
        user = None
        if '@' in login:
            user = User.objects.filter(email__iexact=login).order_by('id').first()
        if user is None:
            user = User.objects.filter(username__iexact=login).order_by('id').first()
        if user is None:
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
