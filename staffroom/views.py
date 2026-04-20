from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_user_wallet


@login_required
def index(request):
    wallet = get_user_wallet(request.user)
    return render(request, 'staffroom/index.html', {'wallet': wallet})
