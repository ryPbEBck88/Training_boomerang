from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .constants import BOOMERANG_GROUP_NAME


def is_boomerang_member(user):
    return (
        user.is_authenticated
        and user.groups.filter(name=BOOMERANG_GROUP_NAME).exists()
    )


def boomerang_member_required(view_func):
    """
    Только авторизованные пользователи в группе «Boomerang».
    Остальные (включая гостей) получают 403 после входа — без группы доступ запрещён.
    """

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not is_boomerang_member(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped
