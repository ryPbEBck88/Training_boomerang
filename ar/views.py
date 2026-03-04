import random
from django.shortcuts import render, redirect
from django.urls import reverse


MULTIPLIER_OPTIONS = [1, 2, 5, 10, 25, 50, 125]
DEFAULT_MULTIPLIERS = [2, 5, 10, 25, 50]


def _parse_int(val, default, lo, hi):
    try:
        v = int(val)
        return max(lo, min(hi, v))
    except (TypeError, ValueError):
        return default


def _gen_number(min_val, max_val, step):
    if min_val >= max_val:
        max_val = min_val + step
    n = (max_val - min_val) // step + 1
    if n <= 0:
        return min_val
    return min_val + random.randint(0, n - 1) * step


def index(request):
    return render(request, 'ar/index.html')


def ar_bets(request):
    mix_mode = request.GET.get('mode') == 'mix'
    return render(request, 'ar/ar_bets.html', {'mix_mode': mix_mode})


def ar_mix(request):
    """Mix: заставка → число x → цвет в cash с числом x → заставка → ..."""
    return redirect(reverse('ar_bets') + '?mode=mix')


def ar_mix_continue(request):
    """После успеха в цвет в cash (mix) — обратно к заставке."""
    request.session.pop('ar_roulette_mix_mode', None)
    request.session.pop('ar_roulette_mix_number', None)
    return redirect(reverse('ar_bets') + '?mode=mix')


def ar_roulette(request):
    """Цвет в cash. Настройки: min, max, step; чекбоксы множителей."""
    if request.GET.get('mode') != 'mix' and 'mix_number' not in request.GET:
        request.session.pop('ar_roulette_mix_mode', None)
        request.session.pop('ar_roulette_mix_number', None)
    mix_mode = request.GET.get('mode') == 'mix' or request.session.get('ar_roulette_mix_mode')
    mix_number = request.GET.get('mix_number') or request.session.get('ar_roulette_mix_number')
    if request.GET.get('mode') == 'mix':
        request.session['ar_roulette_mix_mode'] = True
    if request.GET.get('mix_number'):
        request.session['ar_roulette_mix_number'] = request.GET.get('mix_number')

    min_val = request.session.get('ar_roulette_min', 100)
    max_val = request.session.get('ar_roulette_max', 1000)
    step = request.session.get('ar_roulette_step', 1)
    multipliers = request.session.get('ar_roulette_multipliers', list(DEFAULT_MULTIPLIERS))

    if request.method == 'POST' and request.POST.get('action') == 'settings':
        min_val = _parse_int(request.POST.get('min_val'), min_val, 1, 100000)
        max_val = _parse_int(request.POST.get('max_val'), max_val, 1, 100000)
        step = _parse_int(request.POST.get('step'), step, 1, 10000)
        if min_val >= max_val:
            max_val = min_val + step
        if step > max_val - min_val:
            step = max(1, max_val - min_val)

        multipliers = []
        for m in MULTIPLIER_OPTIONS:
            if request.POST.get(f'mult_{m}') == 'on':
                multipliers.append(m)
        if not multipliers:
            multipliers = list(DEFAULT_MULTIPLIERS)

        request.session['ar_roulette_min'] = min_val
        request.session['ar_roulette_max'] = max_val
        request.session['ar_roulette_step'] = step
        request.session['ar_roulette_multipliers'] = multipliers
        return redirect('ar_roulette')

    number = request.session.get('ar_roulette_current_number')
    multiplier = request.session.get('ar_roulette_current_multiplier')

    if request.method == 'GET' or (request.method == 'POST' and request.POST.get('action') == 'next'):
        if mix_mode and mix_number:
            try:
                number = int(mix_number)
                number = max(1, number)  # sanity
            except (TypeError, ValueError):
                number = _gen_number(min_val, max_val, step)
        else:
            number = _gen_number(min_val, max_val, step)
        multiplier = random.choice(multipliers)
        request.session['ar_roulette_current_number'] = number
        request.session['ar_roulette_current_multiplier'] = multiplier
        return render(request, 'ar/ar_roulette.html', {
            'number': number,
            'multiplier': multiplier,
            'min_val': min_val,
            'max_val': max_val,
            'step': step,
            'multiplier_options': MULTIPLIER_OPTIONS,
            'selected_multipliers': multipliers,
            'mix_mode': mix_mode,
            'message': '',
            'success': None,
            'skipped': False,
        })

    message = ''
    success = None
    skipped = False
    action = request.POST.get('action')
    user_answer = request.POST.get('user_answer', '').strip()
    correct = number * multiplier

    if action == 'skip':
        message = f"Пропущено. Правильный ответ: {correct}"
        success = None
        skipped = True
    elif action == 'check':
        try:
            user_val = int(user_answer)
            if user_val == correct:
                message = "Правильно!"
                success = True
            else:
                message = f"Неправильно! Правильный ответ: {correct}"
                success = False
        except ValueError:
            message = f"Введите число. Правильный ответ: {correct}"
            success = False

    return render(request, 'ar/ar_roulette.html', {
        'number': number,
        'multiplier': multiplier,
        'min_val': min_val,
        'max_val': max_val,
        'step': step,
        'multiplier_options': MULTIPLIER_OPTIONS,
        'selected_multipliers': multipliers,
        'mix_mode': mix_mode,
        'message': message,
        'success': success,
        'skipped': skipped,
    })
