import logging
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from .constants import TIP_THANK_YOU_MESSAGES
from .email_activation import send_activation_email
from .forms import SignUpForm

logger = logging.getLogger(__name__)
User = get_user_model()


def index(request):
    return render(request, 'homepage/index.html')


def chaevye(request):
    return render(
        request,
        'homepage/chaevye.html',
        {'tip_jar_url': settings.TIP_JAR_URL},
    )


def tip_thanks(request):
    return render(
        request,
        'homepage/spasibo.html',
        {'message': random.choice(TIP_THANK_YOU_MESSAGES)},
    )


def authors_page(request):
    return render(request, 'homepage/authors.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('homepage_index')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                send_activation_email(request, user)
            except Exception:
                logger.exception('activation email failed for user_id=%s', user.pk)
                user.delete()
                form.add_error(
                    None,
                    'Не удалось отправить письмо. Проверьте адрес почты или настройки сервера и попробуйте снова.',
                )
            else:
                return redirect('register_verify_sent')
    else:
        form = SignUpForm()
    return render(request, 'registration/register.html', {'form': form})


def register_verify_sent(request):
    if request.user.is_authenticated:
        return redirect('homepage_index')
    return render(request, 'registration/register_verify_sent.html')


def activate_account(request, uidb64, token):
    if request.user.is_authenticated:
        return redirect('homepage_index')
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        return redirect(f'{reverse("login")}?confirmed=1')
    return render(request, 'registration/activation_invalid.html')
