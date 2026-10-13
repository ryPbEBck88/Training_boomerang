import logging
import random
import json
from urllib import parse, request as urlrequest

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from .constants import TIP_THANK_YOU_MESSAGES
from .email_activation import send_activation_email
from .forms import (
    EmailContinueForm,
    LoginIdentifierForm,
    LoginPasswordForm,
    SignUpDetailsForm,
)

logger = logging.getLogger(__name__)
User = get_user_model()

SESSION_REGISTER_EMAIL = 'register_email'
SESSION_LOGIN_ID = 'login_identifier'


def _get_client_ip(request):
    forwarded = (request.META.get('HTTP_X_FORWARDED_FOR') or '').strip()
    if forwarded:
        return forwarded.split(',')[0].strip()
    return (request.META.get('REMOTE_ADDR') or '').strip() or 'unknown'


def _register_rate_limited(request):
    ip = _get_client_ip(request)
    window = max(1, int(getattr(settings, 'REGISTER_RATE_LIMIT_WINDOW', 600)))
    limit = max(1, int(getattr(settings, 'REGISTER_RATE_LIMIT_COUNT', 5)))
    key = f'register:attempts:{ip}'
    attempts = cache.get(key, 0)
    if attempts >= limit:
        return True
    if attempts == 0:
        cache.set(key, 1, timeout=window)
    else:
        cache.incr(key)
    return False


def _verify_turnstile(request):
    secret = (getattr(settings, 'TURNSTILE_SECRET_KEY', '') or '').strip()
    if not secret:
        return True
    token = (request.POST.get('cf-turnstile-response') or '').strip()
    if not token:
        return False
    payload = parse.urlencode(
        {
            'secret': secret,
            'response': token,
            'remoteip': _get_client_ip(request),
        }
    ).encode('utf-8')
    req = urlrequest.Request(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        data=payload,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    try:
        with urlrequest.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception:
        logger.exception('turnstile verification failed')
        return False
    return bool(data.get('success'))


def index(request):
    # Яндекс Redirect URI = корень сайта → сюда приходит ?code=…
    if request.GET.get('code') or request.GET.get('error'):
        qs = request.GET.urlencode()
        return redirect(f'/oauth/complete/yandex-oauth2/?{qs}')
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
    if request.GET.get('restart') == '1':
        request.session.pop(SESSION_REGISTER_EMAIL, None)
        return redirect('register')

    email = (request.session.get(SESSION_REGISTER_EMAIL) or '').strip().lower()
    turnstile_site_key = (getattr(settings, 'TURNSTILE_SITE_KEY', '') or '').strip()
    social_error = request.GET.get('social_error') == '1'

    # Шаг 2: логин + пароль
    if email:
        if request.method == 'POST':
            form = SignUpDetailsForm(request.POST, email=email)
            if _register_rate_limited(request):
                form.add_error(
                    None,
                    'Слишком много попыток регистрации. Подождите несколько минут и попробуйте снова.',
                )
            elif turnstile_site_key and not _verify_turnstile(request):
                form.add_error(None, 'Проверка защиты не пройдена. Обновите страницу и попробуйте снова.')
            elif form.is_valid():
                user = form.save()
                try:
                    send_activation_email(request, user)
                except Exception:
                    logger.exception('activation email failed for user_id=%s', user.pk)
                    form.add_error(
                        None,
                        'Аккаунт создан, но письмо не отправилось. '
                        'Проверьте почту и попробуйте отправить письмо ещё раз.',
                    )
                    request.session['register_pending_user_id'] = user.pk
                    request.session.pop(SESSION_REGISTER_EMAIL, None)
                    return render(
                        request,
                        'registration/register.html',
                        {
                            'step': 'details',
                            'form': form,
                            'email': email,
                            'turnstile_site_key': turnstile_site_key,
                            'social_error': social_error,
                        },
                    )
                request.session['register_pending_user_id'] = user.pk
                request.session.pop(SESSION_REGISTER_EMAIL, None)
                return redirect('register_verify_sent')
        else:
            form = SignUpDetailsForm(email=email)
        return render(
            request,
            'registration/register.html',
            {
                'step': 'details',
                'form': form,
                'email': email,
                'turnstile_site_key': turnstile_site_key,
                'social_error': social_error,
            },
        )

    # Шаг 1: email
    if request.method == 'POST':
        form = EmailContinueForm(request.POST)
        if form.is_valid():
            email_val = form.cleaned_data['email']
            if User.objects.filter(email__iexact=email_val).exists():
                form.add_error(
                    'email',
                    'Этот адрес уже используется. Войдите или укажите другую почту.',
                )
            else:
                request.session[SESSION_REGISTER_EMAIL] = email_val
                return redirect('register')
    else:
        form = EmailContinueForm()
    return render(
        request,
        'registration/register.html',
        {
            'step': 'email',
            'form': form,
            'turnstile_site_key': '',
            'social_error': social_error,
        },
    )


def register_verify_sent(request):
    if request.user.is_authenticated:
        return redirect('homepage_index')
    pending_user_id = request.session.get('register_pending_user_id')
    can_resend = False
    if pending_user_id:
        try:
            user = User.objects.get(pk=pending_user_id)
            can_resend = not user.is_active
        except User.DoesNotExist:
            can_resend = False
    return render(request, 'registration/register_verify_sent.html', {'can_resend': can_resend})


def resend_activation(request):
    if request.user.is_authenticated:
        return redirect('homepage_index')
    if request.method != 'POST':
        return redirect('register_verify_sent')
    pending_user_id = request.session.get('register_pending_user_id')
    if not pending_user_id:
        return redirect('register')
    try:
        user = User.objects.get(pk=pending_user_id)
    except User.DoesNotExist:
        request.session.pop('register_pending_user_id', None)
        return redirect('register')
    if user.is_active:
        request.session.pop('register_pending_user_id', None)
        return redirect(f'{reverse("login")}?confirmed=1')
    try:
        send_activation_email(request, user)
    except Exception:
        logger.exception('activation email resend failed for user_id=%s', user.pk)
        return render(
            request,
            'registration/register_verify_sent.html',
            {
                'can_resend': True,
                'resend_error': (
                    'Письмо снова не отправилось. Проверьте адрес или настройки почты и повторите попытку.'
                ),
            },
        )
    return render(
        request,
        'registration/register_verify_sent.html',
        {'can_resend': True, 'resend_ok': 'Письмо отправлено повторно. Проверьте почту.'},
    )


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


def login_view(request):
    if request.user.is_authenticated:
        return redirect('homepage_index')
    # Старый ярлык ?signup=1 → отдельная страница регистрации
    if request.GET.get('signup') == '1':
        return redirect('register')
    if request.GET.get('restart') == '1':
        request.session.pop(SESSION_LOGIN_ID, None)
        return redirect('login')

    identifier = (request.session.get(SESSION_LOGIN_ID) or '').strip()
    confirmed = request.GET.get('confirmed') == '1'
    social_error = request.GET.get('social_error') == '1'

    # Шаг 2: пароль
    if identifier:
        if request.method == 'POST':
            form = LoginPasswordForm(request.POST)
            if form.is_valid():
                user = authenticate(
                    request,
                    username=identifier,
                    password=form.cleaned_data['password'],
                )
                if user is not None:
                    login(request, user)
                    request.session.pop(SESSION_LOGIN_ID, None)
                    next_url = request.GET.get('next') or request.POST.get('next') or '/'
                    if next_url.startswith('/'):
                        return redirect(next_url)
                    return redirect('homepage_index')
                form.add_error(None, 'Неверный пароль. Проверьте ввод или подтвердите почту после регистрации.')
        else:
            form = LoginPasswordForm()
        return render(
            request,
            'registration/login.html',
            {
                'step': 'password',
                'form': form,
                'identifier': identifier,
                'confirmed': confirmed,
                'social_error': social_error,
                'next': request.GET.get('next', ''),
            },
        )

    # Шаг 1: идентификатор
    if request.method == 'POST':
        form = LoginIdentifierForm(request.POST)
        if form.is_valid():
            request.session[SESSION_LOGIN_ID] = form.cleaned_data['identifier']
            return redirect('login')
    else:
        form = LoginIdentifierForm()
    return render(
        request,
        'registration/login.html',
        {
            'step': 'identifier',
            'form': form,
            'confirmed': confirmed,
            'social_error': social_error,
            'next': request.GET.get('next', ''),
        },
    )
