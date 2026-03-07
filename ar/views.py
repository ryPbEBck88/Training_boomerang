import math
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


def ar_mix_to_ptc(request):
    """Mix: после успеха в цвет в cash — в выплату через кеш (цвет + цвет_по)."""
    if request.method != 'POST':
        return redirect('ar_bets')
    mix_color = request.POST.get('mix_number')  # число от заставки = цвет
    mix_color_per = request.POST.get('mix_multiplier')  # множитель = цвет по
    try:
        mix_color = int(mix_color) if mix_color else None
        mix_color_per = int(mix_color_per) if mix_color_per else None
    except (TypeError, ValueError):
        mix_color = mix_color_per = None
    if mix_color is not None and mix_color > 0 and mix_color_per is not None and mix_color_per > 0:
        request.session['ar_ptc_mix_color'] = mix_color
        request.session['ar_ptc_mix_color_per'] = mix_color_per
    request.session.pop('ar_roulette_mix_mode', None)
    request.session.pop('ar_roulette_mix_number', None)
    return redirect(reverse('ar_payout_through_cash') + '?mode=mix')


def ar_mix_continue(request):
    """После успеха в выплате через кеш (mix) — обратно к заставке."""
    request.session.pop('ar_roulette_mix_mode', None)
    request.session.pop('ar_roulette_mix_number', None)
    request.session.pop('ar_ptc_mix_color', None)
    request.session.pop('ar_ptc_mix_color_per', None)
    request.session.pop('ar_ptc_mix_mode', None)
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
        return redirect('ar_color_in_cash')

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


COLOR_PER_OPTIONS = [2, 5, 10, 25, 50, 100, 125]
DEFAULT_COLOR_PER = [5, 10, 25]


def ar_payout_through_cash(request):
    """Выплата через кеш: цвет, cash, цвет по. Сколько цветных фишек осталось? ответ = цвет - (cash / цвет_по), 1–200."""
    mix_mode = request.GET.get('mode') == 'mix' or request.session.get('ar_ptc_mix_mode')
    if request.GET.get('mode') == 'mix':
        request.session['ar_ptc_mix_mode'] = True

    min_val = request.session.get('ar_ptc_min', 50)
    max_val = request.session.get('ar_ptc_max', 500)
    step = request.session.get('ar_ptc_step', 10)
    color_per_opts = request.session.get('ar_ptc_color_per', list(DEFAULT_COLOR_PER))
    use_stacks = request.session.get('ar_ptc_use_stacks', False)
    stack_size = 20  # фиксировано

    if request.method == 'POST' and request.POST.get('action') == 'settings':
        min_val = _parse_int(request.POST.get('min_val'), min_val, 1, 10000)
        max_val = _parse_int(request.POST.get('max_val'), max_val, 1, 10000)
        step = _parse_int(request.POST.get('step'), step, 1, 1000)
        if min_val >= max_val:
            max_val = min_val + step
        if step > max_val - min_val:
            step = max(1, max_val - min_val)
        color_per_opts = []
        for c in COLOR_PER_OPTIONS:
            if request.POST.get(f'color_per_{c}') == 'on':
                color_per_opts.append(c)
        if not color_per_opts:
            color_per_opts = list(DEFAULT_COLOR_PER)
        use_stacks = request.POST.get('ar_ptc_use_stacks') == 'on'
        request.session['ar_ptc_min'] = min_val
        request.session['ar_ptc_max'] = max_val
        request.session['ar_ptc_step'] = step
        request.session['ar_ptc_color_per'] = color_per_opts
        request.session['ar_ptc_use_stacks'] = use_stacks
        return redirect('ar_payout_through_cash')

    color = request.session.get('ar_ptc_color')
    color_per = request.session.get('ar_ptc_color_per_val')
    cash = request.session.get('ar_ptc_cash')

    if request.method == 'GET' or (request.method == 'POST' and request.POST.get('action') == 'next'):
        if mix_mode:
            color = request.session.get('ar_ptc_mix_color')
            color_per = request.session.get('ar_ptc_mix_color_per')
            if not color or not color_per or color < 2:
                request.session.pop('ar_ptc_mix_mode', None)
                return redirect(reverse('ar_bets') + '?mode=mix')
        else:
            color_per = random.choice(color_per_opts)
            color = max(2, _gen_number(min_val, max_val, step))
        # cash должно делиться на step (при step 100 — cash 7700, 7800, а не 7725)
        step_gcd = math.gcd(step, color_per)
        chips_increment = step // step_gcd
        chips_paid_min = max(1, color - 200)
        chips_paid_max = color - 1
        valid_starts = range(
            ((chips_paid_min + chips_increment - 1) // chips_increment) * chips_increment,
            chips_paid_max + 1,
            chips_increment,
        )
        valid_list = [c for c in valid_starts if chips_paid_min <= c <= chips_paid_max]
        if valid_list:
            chips_paid = random.choice(valid_list)
        else:
            chips_paid = color - random.randint(1, min(200, color - 1))
        remaining = color - chips_paid
        cash = chips_paid * color_per
        request.session['ar_ptc_color'] = color
        request.session['ar_ptc_color_per_val'] = color_per
        request.session['ar_ptc_cash'] = cash
        return render(request, 'ar/ar_payout_through_cash.html', {
            'color': color,
            'color_per': color_per,
            'cash': cash,
            'min_val': min_val,
            'max_val': max_val,
            'step': step,
            'color_per_options': COLOR_PER_OPTIONS,
            'selected_color_per': color_per_opts,
            'use_stacks': use_stacks,
            'stack_size': stack_size,
            'mix_mode': mix_mode,
            'message': '',
            'success': None,
            'skipped': False,
        })

    message = ''
    success = None
    skipped = False
    action = request.POST.get('action')
    correct = color - (cash // color_per)

    if action == 'skip':
        if use_stacks:
            correct_stacks = correct // stack_size
            correct_remainder = correct % stack_size
            message = f"Пропущено. Правильный ответ: {correct_stacks} стеков, {correct_remainder} в неполном"
        else:
            message = f"Пропущено. Правильный ответ: {correct}"
        success = None
        skipped = True
    elif action == 'check':
        if use_stacks:
            user_stacks = request.POST.get('user_answer_stacks', '').strip()
            user_remainder = request.POST.get('user_answer_remainder', '').strip()
            try:
                stacks_val = int(user_stacks) if user_stacks else None
                rem_val = int(user_remainder) if user_remainder else None
                if stacks_val is not None and rem_val is not None and rem_val >= 0 and rem_val < stack_size:
                    user_total = stacks_val * stack_size + rem_val
                    if user_total == correct:
                        message = "Правильно!"
                        success = True
                    else:
                        correct_stacks = correct // stack_size
                        correct_remainder = correct % stack_size
                        message = f"Неправильно! Правильный ответ: {correct_stacks} стеков, {correct_remainder} в неполном"
                        success = False
                else:
                    correct_stacks = correct // stack_size
                    correct_remainder = correct % stack_size
                    message = f"Введите стеков (целое) и в неполном (0–{stack_size - 1}). Правильный ответ: {correct_stacks} стеков, {correct_remainder} в неполном"
                    success = False
            except ValueError:
                correct_stacks = correct // stack_size
                correct_remainder = correct % stack_size
                message = f"Введите числа. Правильный ответ: {correct_stacks} стеков, {correct_remainder} в неполном"
                success = False
        else:
            user_answer = request.POST.get('user_answer', '').strip()
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

    return render(request, 'ar/ar_payout_through_cash.html', {
        'color': color,
        'color_per': color_per,
        'cash': cash,
        'min_val': min_val,
        'max_val': max_val,
        'step': step,
        'color_per_options': COLOR_PER_OPTIONS,
        'selected_color_per': color_per_opts,
        'use_stacks': use_stacks,
        'stack_size': stack_size,
        'mix_mode': mix_mode,
        'message': message,
        'success': success,
        'skipped': skipped,
    })
