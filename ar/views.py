import math
import random
from django.shortcuts import render, redirect
from django.urls import reverse
from training.utils.timer import process_timer_settings


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


# Порядок чисел на колесе рулетки (по часовой стрелке)
ROULETTE_WHEEL = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]


def _wheel_neighbors(center):
    """Для числа center возвращает (ccw2, ccw1, cw1, cw2) по колесу."""
    try:
        idx = ROULETTE_WHEEL.index(center)
    except ValueError:
        return (None, None, None, None)
    n = len(ROULETTE_WHEEL)
    ccw2 = ROULETTE_WHEEL[(idx - 2) % n]
    ccw1 = ROULETTE_WHEEL[(idx - 1) % n]
    cw1 = ROULETTE_WHEEL[(idx + 1) % n]
    cw2 = ROULETTE_WHEEL[(idx + 2) % n]
    return (ccw2, ccw1, cw1, cw2)


def index(request):
    return render(request, 'ar/index.html')


def ar_bets(request):
    mix_mode = request.GET.get('mode') == 'mix'
    timer_enabled = request.session.get('timer_enabled', True)
    timer_seconds = request.session.get('timer_seconds', 10)
    return render(request, 'ar/ar_bets.html', {
        'mix_mode': mix_mode,
        'timer_enabled': timer_enabled,
        'timer_seconds': timer_seconds,
    })


def ar_neighbors(request):
    """Соседи: 5 ячеек, центр 0–36, ввести 4 соседа по колесу. По часовой — чек, против — почти чек."""
    if request.method == 'GET' or (request.method == 'POST' and request.POST.get('action') == 'next'):
        center = random.randint(0, 36)
        ccw2, ccw1, cw1, cw2 = _wheel_neighbors(center)
        request.session['ar_neighbors_center'] = center
        request.session['ar_neighbors_ccw2'] = ccw2
        request.session['ar_neighbors_ccw1'] = ccw1
        request.session['ar_neighbors_cw1'] = cw1
        request.session['ar_neighbors_cw2'] = cw2
        return render(request, 'ar/ar_neighbors.html', {
            'center': center,
            'message': '',
            'success': None,
            'skipped': False,
            'user_cell1': '',
            'user_cell2': '',
            'user_cell4': '',
            'user_cell5': '',
        })

    center = request.session.get('ar_neighbors_center', 0)
    ccw2, ccw1, cw1, cw2 = (
        request.session.get('ar_neighbors_ccw2'),
        request.session.get('ar_neighbors_ccw1'),
        request.session.get('ar_neighbors_cw1'),
        request.session.get('ar_neighbors_cw2'),
    )
    message = ''
    success = None
    skipped = False

    def _parse_cell(val):
        try:
            v = int(val) if val else None
            return v if v is not None and 0 <= v <= 36 else None
        except (TypeError, ValueError):
            return None

    if request.POST.get('action') == 'skip':
        message = f"Пропущено. Правильно: {ccw2} | {ccw1} | {center} | {cw1} | {cw2}"
        success = None
        skipped = True
    elif request.POST.get('action') == 'check':
        u1 = _parse_cell(request.POST.get('cell1'))
        u2 = _parse_cell(request.POST.get('cell2'))
        u4 = _parse_cell(request.POST.get('cell4'))
        u5 = _parse_cell(request.POST.get('cell5'))
        if u1 is None or u2 is None or u4 is None or u5 is None:
            message = "Введите все 4 числа"
            success = None
        else:
            # Стандартный порядок (чек): [CCW2, CCW1, center, CW1, CW2] — напр. 26 0 32 15 19
            standard_ok = (u1 == ccw2 and u2 == ccw1 and u4 == cw1 and u5 == cw2)
            # По часовой (чек): [CW2, CW1, center, CCW2, CCW1] — напр. 10 5 24 16 33
            cw_order_ok = (u1 == cw2 and u2 == cw1 and u4 == ccw2 and u5 == ccw1)
            # По часовой, правая пара в обратном порядке: [CW2, CW1, center, CCW1, CCW2] — напр. 0 26 3 35 12 (почти чек)
            cw_order_rev_ok = (u1 == cw2 and u2 == cw1 and u4 == ccw1 and u5 == ccw2)
            # Против часовой (почти чек): [CCW1, CCW2, center, CW1, CW2] — напр. 33 16 24 5 10
            ccw_order_ok = (u1 == ccw1 and u2 == ccw2 and u4 == cw1 and u5 == cw2)
            if standard_ok or cw_order_ok:
                message = "Правильно!"
                success = 'full'
            elif ccw_order_ok or cw_order_rev_ok:
                message = "👍 Почти! Правильно по часовой стрелке."
                success = 'almost'
            else:
                message = ""
                success = False

    return render(request, 'ar/ar_neighbors.html', {
        'center': center,
        'message': message,
        'success': success,
        'skipped': skipped,
        'user_cell1': request.POST.get('cell1', ''),
        'user_cell2': request.POST.get('cell2', ''),
        'user_cell4': request.POST.get('cell4', ''),
        'user_cell5': request.POST.get('cell5', ''),
    })


# Таблица комплитов: (chips_count, payout_mult) по номеру
# payout = payout_mult × (total / chips_count) = payout_mult × chip_value
COMPLETE_TABLE = {
    0: (17, 235),
    1: (27, 297), 3: (27, 297),
    2: (36, 396),
    4: (30, 294), 7: (30, 294), 10: (30, 294), 13: (30, 294), 16: (30, 294),
    19: (30, 294), 22: (30, 294), 25: (30, 294), 28: (30, 294), 31: (30, 294),
    6: (30, 294), 9: (30, 294), 12: (30, 294), 15: (30, 294), 18: (30, 294),
    21: (30, 294), 24: (30, 294), 27: (30, 294), 30: (30, 294), 33: (30, 294),
    5: (40, 392), 8: (40, 392), 11: (40, 392), 14: (40, 392), 17: (40, 392),
    20: (40, 392), 23: (40, 392), 26: (40, 392), 29: (40, 392), 32: (40, 392),
    34: (18, 198), 36: (18, 198),
    35: (24, 264),
}
COMPLETE_DENOMINATIONS_DEFAULT = [25, 50, 75, 100, 200, 300, 400, 500]
COMPLETE_DENOMINATIONS_ALL = [25, 50, 75, 100, 150, 200, 250, 300, 400, 500]

# Группы номеров для комплитов (ключ, подпись, список номеров)
COMPLETE_NUMBER_GROUPS = [
    ('0', '0', [0]),
    ('1_3', '1, 3', [1, 3]),
    ('2', '2', [2]),
    ('34_36', '34, 36', [34, 36]),
    ('35', '35', [35]),
    ('4_31', 'column 4-31', [4, 7, 10, 13, 16, 19, 22, 25, 28, 31]),
    ('6_33', 'column 6-33', [6, 9, 12, 15, 18, 21, 24, 27, 30, 33]),
    ('5_32', 'column 5-32', [5, 8, 11, 14, 17, 20, 23, 26, 29, 32]),
]


def _get_complete_denominations(request):
    """Номиналы из сессии или по умолчанию."""
    stored = request.session.get('ar_complete_denominations')
    if stored and isinstance(stored, list) and len(stored) > 0:
        valid = [d for d in stored if d in COMPLETE_DENOMINATIONS_ALL]
        if valid:
            return valid
    return COMPLETE_DENOMINATIONS_DEFAULT


def _get_complete_numbers(request):
    """Номера 0–36 из сессии или по умолчанию все."""
    stored = request.session.get('ar_complete_numbers')
    if stored and isinstance(stored, list) and len(stored) > 0:
        valid = [n for n in stored if isinstance(n, int) and 0 <= n <= 36]
        if valid:
            return sorted(valid)
    return list(range(37))  # 0–36


def _selected_group_keys(selected_numbers):
    """Ключи групп, которые выбраны (все их номера в selected_numbers)."""
    return {k for k, _l, nums in COMPLETE_NUMBER_GROUPS
            if all(n in selected_numbers for n in nums)}


def ar_completes(request):
    """Комплиты: выпал номер N, комплит по X — ввести ставку и выплату."""
    if request.method == 'POST' and request.POST.get('action') == 'settings':
        selected_d = []
        for d in COMPLETE_DENOMINATIONS_ALL:
            if request.POST.get('denom_%d' % d) == 'on':
                selected_d.append(d)
        if selected_d:
            request.session['ar_complete_denominations'] = sorted(selected_d)
        else:
            request.session['ar_complete_denominations'] = COMPLETE_DENOMINATIONS_DEFAULT
        selected_n = []
        for key, _label, nums in COMPLETE_NUMBER_GROUPS:
            if request.POST.get('group_%s' % key) == 'on':
                selected_n.extend(nums)
        if selected_n:
            request.session['ar_complete_numbers'] = sorted(set(selected_n))
        else:
            request.session['ar_complete_numbers'] = list(range(37))
        return redirect(reverse('ar_completes'))

    denoms = _get_complete_denominations(request)
    numbers = _get_complete_numbers(request)
    if request.method == 'GET' or (request.method == 'POST' and request.POST.get('action') == 'next'):
        number = random.choice(numbers)
        denom = random.choice(denoms)
        chips, mult = COMPLETE_TABLE[number]
        total = chips * denom
        payout = mult * denom
        request.session['ar_complete_number'] = number
        request.session['ar_complete_denom'] = denom
        request.session['ar_complete_total'] = total
        request.session['ar_complete_payout'] = payout
        return render(request, 'ar/ar_completes.html', {
            'number': number,
            'denom': denom,
            'message': '',
            'success': None,
            'skipped': False,
            'user_stavka': '',
            'user_payout': '',
            'denominations_all': COMPLETE_DENOMINATIONS_ALL,
            'selected_denoms': denoms,
            'selected_numbers': numbers,
            'number_groups': COMPLETE_NUMBER_GROUPS,
            'selected_group_keys': _selected_group_keys(numbers),
        })

    number = request.session.get('ar_complete_number', 0)
    denom = request.session.get('ar_complete_denom', 100)
    correct_total = request.session.get('ar_complete_total', 0)
    correct_payout = request.session.get('ar_complete_payout', 0)
    message = ''
    success = None
    skipped = False

    if request.POST.get('action') == 'skip':
        message = f'Пропущено. Ставка: {correct_total}, выплата: {correct_payout}'
        skipped = True
    elif request.POST.get('action') == 'check':
        try:
            user_stavka = int(request.POST.get('stavka', '').replace(' ', ''))
        except (TypeError, ValueError):
            user_stavka = None
        try:
            user_payout = int(request.POST.get('payout', '').replace(' ', ''))
        except (TypeError, ValueError):
            user_payout = None
        if user_stavka is None or user_payout is None:
            message = 'Введите ставку и выплату'
        elif user_stavka == correct_total and user_payout == correct_payout:
            message = 'Правильно!'
            success = True
        else:
            errors = []
            if user_stavka != correct_total:
                errors.append(f'ставка {correct_total}')
            if user_payout != correct_payout:
                errors.append(f'выплата {correct_payout}')
            message = f'Нет. Правильно: {", ".join(errors)}'
            success = False

    return render(request, 'ar/ar_completes.html', {
        'number': number,
        'denom': denom,
        'message': message,
        'success': success,
        'skipped': skipped,
        'user_stavka': request.POST.get('stavka', ''),
        'user_payout': request.POST.get('payout', ''),
        'denominations_all': COMPLETE_DENOMINATIONS_ALL,
        'selected_denoms': _get_complete_denominations(request),
        'selected_numbers': _get_complete_numbers(request),
        'number_groups': COMPLETE_NUMBER_GROUPS,
        'selected_group_keys': _selected_group_keys(_get_complete_numbers(request)),
    })


def ar_mix(request):
    """Mix: заставка → число x → цвет в cash с числом x → заставка → ..."""
    return redirect(reverse('ar_bets') + '?mode=mix')


def ar_mix_to_ptc(request):
    """Mix: после успеха в цвет в cash — в выплату через cash (цвет + цвет_по)."""
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
    """После успеха в выплате через cash (mix) — обратно к заставке."""
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
        process_timer_settings(request)
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
    """Выплата через cash: цвет, cash, цвет по. Сколько цветных фишек осталось? ответ = цвет - (cash / цвет_по), 1–200."""
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
        process_timer_settings(request)
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
                # пустое поле = 0 (ноль писать не обязательно)
                stacks_val = int(user_stacks) if user_stacks else 0
                rem_val = int(user_remainder) if user_remainder else 0
                if rem_val >= 0 and rem_val < stack_size:
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
