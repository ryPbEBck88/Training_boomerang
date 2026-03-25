import json
import math
import random
import time
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


def ar_series(request):
    """Серии на колесе: поле сверху, подсветка tiers / orphelins / voisins / jeu zéro."""
    return render(request, 'ar/ar_series.html')


def ar_bet_reveal(request):
    """Тренажёр: стопки на поле — клик в порядке раскрытия (напр. выигрышное число 5)."""
    timer_enabled = request.session.get('timer_enabled', True)
    timer_seconds = request.session.get('timer_seconds', 10)
    return render(request, 'ar/ar_bet_reveal.html', {
        'timer_enabled': timer_enabled,
        'timer_seconds': timer_seconds,
    })


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


SERIES_STAKE_AR_PRESET_DEFAULT = '1-100-1'
SERIES_STAKE_AR_CUSTOM = 'custom'
# Рандом AR: каждый новый раунд — случайный пресет из SERIES_STAKE_AR_PRESETS.
SERIES_STAKE_AR_RANDOM = 'ar_random'
SERIES_STAKE_AR_PRESETS = [
    '1-100-1',
    '2-200-5',
    '5-300-5',
    '10-500-5',
    '25-500-5',
]

# Шаг случайной ставки (Tiers) по умолчанию — одинаковый для всех пресетов AR.
SERIES_STAKE_DEFAULT_STAKE_STEP = 5
SERIES_STAKE_TIMER_DEFAULT_ENABLED = True
SERIES_STAKE_TIMER_DEFAULT_SECONDS = 30
SERIES_STAKE_TIMER_SECONDS_MAX = 120

# Границы суммы ставки по серии: min = min_серии × первый множитель, max = max_номера × второй.
SERIES_STAKE_BET_BOUNDS_SMP = {
    'tiers': 6,
    'zero': 4,
    'orphelins': 5,
    'voisins': 9,
}
SERIES_STAKE_BET_BOUNDS_NMAX = {
    'tiers': 12,
    'zero': 7,
    'orphelins': 9,
    'voisins': 17,
}
SERIES_STAKE_RANDOM_BET_SMP_MUL = min(SERIES_STAKE_BET_BOUNDS_SMP.values())
SERIES_STAKE_RANDOM_BET_NMAX_MUL = max(SERIES_STAKE_BET_BOUNDS_NMAX.values())


def _parse_series_stake_ar_triple(preset_id):
    """Пресет «a-b-c»: номер min–max, для серий min по и step = c."""
    if preset_id not in SERIES_STAKE_AR_PRESETS:
        return None
    parts = str(preset_id).split('-')
    if len(parts) != 3:
        return None
    try:
        a, b, c = int(parts[0]), int(parts[1]), int(parts[2])
    except (TypeError, ValueError):
        return None
    return {
        'num_min': a,
        'num_max': b,
        'series_min_po': c,
        'series_step': c,
    }


def _get_series_stake_ar_preset(request):
    s = request.session.get('ar_series_stake_ar_preset')
    if s == SERIES_STAKE_AR_CUSTOM:
        return SERIES_STAKE_AR_CUSTOM
    if s == SERIES_STAKE_AR_RANDOM:
        return SERIES_STAKE_AR_RANDOM
    if s in SERIES_STAKE_AR_PRESETS:
        return s
    return SERIES_STAKE_AR_PRESET_DEFAULT


def _clamp_int(val, lo, hi, default):
    try:
        v = int(val)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def _get_series_stake_timer(request):
    raw_en = request.session.get(
        'ar_series_stake_timer_enabled',
        SERIES_STAKE_TIMER_DEFAULT_ENABLED,
    )
    if isinstance(raw_en, str):
        enabled = raw_en.strip().lower() in ('1', 'true', 'on', 'yes')
    else:
        enabled = bool(raw_en)
    sec = request.session.get(
        'ar_series_stake_timer_seconds',
        SERIES_STAKE_TIMER_DEFAULT_SECONDS,
    )
    sec = _clamp_int(
        sec,
        1,
        SERIES_STAKE_TIMER_SECONDS_MAX,
        SERIES_STAKE_TIMER_DEFAULT_SECONDS,
    )
    return enabled, sec


def _get_series_stake_ar_params(request):
    """Текущие числа для настроек AR (из пресета или пользовательских)."""
    preset = _get_series_stake_ar_preset(request)
    if preset == SERIES_STAKE_AR_CUSTOM:
        d_nm, d_xm, d_smp, d_st = 1, 100, 1, 1
        nm = _clamp_int(request.session.get('ar_series_stake_num_min'), 1, 9999, d_nm)
        xm = _clamp_int(request.session.get('ar_series_stake_num_max'), 1, 9999, d_xm)
        if nm > xm:
            nm, xm = xm, nm
        smp = _clamp_int(request.session.get('ar_series_stake_series_min_po'), 1, 9999, d_smp)
        st = _clamp_int(request.session.get('ar_series_stake_series_step'), 1, 9999, d_st)
        return {
            'num_min': nm,
            'num_max': xm,
            'series_min_po': smp,
            'series_step': st,
        }
    if preset == SERIES_STAKE_AR_RANDOM:
        cached = request.session.get('ar_series_stake_ar_roll_cached')
        if not cached:
            pick = random.choice(SERIES_STAKE_AR_PRESETS)
            cached = _parse_series_stake_ar_triple(pick)
            request.session['ar_series_stake_ar_roll_cached'] = cached
            request.session['ar_series_stake_ar_roll_preset_id'] = pick
        return dict(cached)
    parsed = _parse_series_stake_ar_triple(preset)
    if parsed:
        return parsed
    return _parse_series_stake_ar_triple(SERIES_STAKE_AR_PRESET_DEFAULT)


def _series_stake_min_base(ar_params):
    """
    База для min ставки: сравниваем «серии играют по» min и «номер min», берём большее.
    Пример AR 25-500-5: 25 > 5 → база 25; Tiers min ставки = 25 × 6 = 150 (не 5 × 6 = 30).
    """
    smp = int(ar_params['series_min_po'])
    nmin = int(ar_params['num_min']) if 'num_min' in ar_params else smp
    return smp if smp > nmin else nmin


def _series_stake_stake_by_series(ar_params):
    """Дефолты полей «Ставка» по каждому режиму серии (и рандом — огибающая)."""
    base = _series_stake_min_base(ar_params)
    nmax = ar_params['num_max']
    out = {}
    for key in SERIES_STAKE_BET_BOUNDS_SMP:
        sm_mul = SERIES_STAKE_BET_BOUNDS_SMP[key]
        nm_mul = SERIES_STAKE_BET_BOUNDS_NMAX[key]
        out[key] = {
            'min': base * sm_mul,
            'max': nmax * nm_mul,
            'step': SERIES_STAKE_DEFAULT_STAKE_STEP,
        }
    out['random'] = {
        'min': base * SERIES_STAKE_RANDOM_BET_SMP_MUL,
        'max': nmax * SERIES_STAKE_RANDOM_BET_NMAX_MUL,
        'step': SERIES_STAKE_DEFAULT_STAKE_STEP,
    }
    return out


def _series_stake_preset_map_for_json():
    """Пресеты AR + поля формы; «Ставка» по каждой серии — в stake_by_series."""
    out = {}
    for p in SERIES_STAKE_AR_PRESETS:
        parsed = _parse_series_stake_ar_triple(p)
        if not parsed:
            continue
        smp = parsed['series_min_po']
        xm = parsed['num_max']
        by_s = _series_stake_stake_by_series({
            'series_min_po': smp,
            'num_max': xm,
            'num_min': parsed['num_min'],
        })
        out[p] = {
            'num_min': parsed['num_min'],
            'num_max': xm,
            'series_min_po': smp,
            'series_step': parsed['series_step'],
            'stake_by_series': by_s,
            'stake_min': by_s['tiers']['min'],
            'stake_max': by_s['tiers']['max'],
            'stake_step': SERIES_STAKE_DEFAULT_STAKE_STEP,
        }
    return out


def _series_stake_stake_defaults_for_mode(series_mode, ar_params):
    """Дефолты «Ставка» для выбранного в настройках режима серии (вкл. рандом)."""
    by_s = _series_stake_stake_by_series(ar_params)
    if series_mode in by_s:
        s = by_s[series_mode]
        return {'stake_min': s['min'], 'stake_max': s['max'], 'stake_step': s['step']}
    return by_s['tiers']


def _series_stake_envelope_for_series_key(series_key, ar_params):
    """Допустимый коридор суммы для конкретной серии раунда (ключ из SERIES_STAKE_SERIES_KEYS_POOL)."""
    base = _series_stake_min_base(ar_params)
    nmax = ar_params['num_max']
    sm_mul = SERIES_STAKE_BET_BOUNDS_SMP.get(series_key, SERIES_STAKE_BET_BOUNDS_SMP['tiers'])
    nm_mul = SERIES_STAKE_BET_BOUNDS_NMAX.get(series_key, SERIES_STAKE_BET_BOUNDS_NMAX['tiers'])
    return {
        'stake_min': base * sm_mul,
        'stake_max': nmax * nm_mul,
        'stake_step': SERIES_STAKE_DEFAULT_STAKE_STEP,
    }


def _series_stake_effective_pick_params(request, round_series_key, ar_params):
    """Пересечение настроек пользователя с коридором серии раунда."""
    env = _series_stake_envelope_for_series_key(round_series_key, ar_params)
    user = _get_series_stake_stake_params(request)
    lo = max(user['stake_min'], env['stake_min'])
    hi = min(user['stake_max'], env['stake_max'])
    if lo > hi:
        lo, hi = env['stake_min'], env['stake_max']
    return {'stake_min': lo, 'stake_max': hi, 'stake_step': user['stake_step']}


def _series_stake_bounds_mul_client_json():
    m = {
        k: [SERIES_STAKE_BET_BOUNDS_SMP[k], SERIES_STAKE_BET_BOUNDS_NMAX[k]]
        for k in SERIES_STAKE_BET_BOUNDS_SMP
    }
    m['random'] = [SERIES_STAKE_RANDOM_BET_SMP_MUL, SERIES_STAKE_RANDOM_BET_NMAX_MUL]
    return json.dumps(
        {'mul': m, 'default_step': SERIES_STAKE_DEFAULT_STAKE_STEP},
        ensure_ascii=False,
    )


def _get_series_stake_stake_params(request):
    p = _get_series_stake_ar_params(request)
    mode = _get_series_stake_series_mode(request)
    d = _series_stake_stake_defaults_for_mode(mode, p)
    sm = _clamp_int(request.session.get('ar_series_stake_stake_min'), 1, 999999, d['stake_min'])
    sx = _clamp_int(request.session.get('ar_series_stake_stake_max'), 1, 999999, d['stake_max'])
    ss = _clamp_int(request.session.get('ar_series_stake_stake_step'), 1, 999999, d['stake_step'])
    # Не даём устаревшему значению из сессии быть ниже минимума по текущим AR/серии (раньше могло быть 5×6).
    sm = max(sm, d['stake_min'])
    sx = max(sx, sm)
    return {'stake_min': sm, 'stake_max': sx, 'stake_step': ss}


def _pick_random_stake_amount(lo, hi, step):
    step = max(1, int(step))
    lo, hi = int(lo), int(hi)
    if lo > hi:
        lo, hi = hi, lo
    rem = lo % step
    start = lo if rem == 0 else lo + (step - rem)
    if start > hi:
        return lo
    n = (hi - start) // step + 1
    return start + random.randint(0, n - 1) * step


def _series_stake_template_ctx(request, extra=None):
    params = _get_series_stake_ar_params(request)
    preset = _get_series_stake_ar_preset(request)
    stake = _get_series_stake_stake_params(request)
    preset_map = _series_stake_preset_map_for_json()
    round_sk = request.session.get('ar_series_stake_series_key')
    round_series_label = (
        SERIES_STAKE_SERIES_LABEL.get(round_sk) if round_sk else None
    )
    t_en, t_sec = _get_series_stake_timer(request)
    ctx = {
        'ar_presets': SERIES_STAKE_AR_PRESETS,
        'ar_custom_value': SERIES_STAKE_AR_CUSTOM,
        'ar_random_value': SERIES_STAKE_AR_RANDOM,
        'selected_ar_preset': preset,
        'ar_params_editable': preset == SERIES_STAKE_AR_CUSTOM,
        'num_min': params['num_min'],
        'num_max': params['num_max'],
        'series_min_po': params['series_min_po'],
        'series_step': params['series_step'],
        'stake_min': stake['stake_min'],
        'stake_max': stake['stake_max'],
        'stake_step': stake['stake_step'],
        'ar_display_short': 'AR %d-%d' % (params['num_min'], params['num_max']),
        'round_series_label': round_series_label,
        'ar_preset_params_json': json.dumps(preset_map, ensure_ascii=False),
        'series_stake_bounds_mul_json': _series_stake_bounds_mul_client_json(),
        'series_stake_series_choices': SERIES_STAKE_SERIES_CHOICES,
        'selected_series_mode': _get_series_stake_series_mode(request),
        'timer_enabled': t_en,
        'timer_seconds': t_sec,
        'solve_seconds': None,
    }
    if extra:
        ctx.update(extra)
    return ctx


SERIES_STAKE_SERIES_RANDOM = 'random'
SERIES_STAKE_SERIES_CHOICES = [
    (SERIES_STAKE_SERIES_RANDOM, 'Рандом'),
    ('tiers', 'Series 5/8 (Tiers)'),
    ('orphelins', 'Orphelins'),
    ('voisins', 'Series 0/2/3 (Voisins)'),
    ('zero', '0-spiel'),
]
SERIES_STAKE_SERIES_LABEL = dict(SERIES_STAKE_SERIES_CHOICES)
SERIES_STAKE_VALID_SERIES_MODES = frozenset(k for k, _ in SERIES_STAKE_SERIES_CHOICES)

SERIES_STAKE_TASK_PLACEHOLDER = 'Условие задания будет здесь — логика тренажёра задаётся отдельно.'

SERIES_STAKE_SERIES_KEYS_POOL = ('tiers', 'orphelins', 'voisins', 'zero')
SERIES_STAKE_TIERS_SPLITS = 6
# 0-spiel / Orphelins: порог и «вторая фаза» после порога.
SERIES_STAKE_ZERO_PRIMARY_SPLITS = 4
SERIES_STAKE_ZERO_THRESHOLD_NMAX_MUL = 4
SERIES_STAKE_ZERO_PHASE2_SPLITS = 3
SERIES_STAKE_ORPHELINS_PRIMARY_SPLITS = 5
SERIES_STAKE_ORPHELINS_THRESHOLD_NMAX_MUL = 5
SERIES_STAKE_ORPHELINS_PHASE2_SPLITS = 4
# Voisins: порог = номер max × 1.5 × 9; пакет до порога 9, после — 7 (шаг серии в основе пакета).
SERIES_STAKE_VOISINS_PRIMARY_SPLITS = 9
SERIES_STAKE_VOISINS_PHASE2_SPLITS = 7


def _get_series_stake_series_mode(request):
    s = request.session.get('ar_series_stake_series_mode')
    if s in SERIES_STAKE_VALID_SERIES_MODES:
        return s
    return SERIES_STAKE_SERIES_RANDOM


def _resolve_series_stake_series_key(request):
    mode = _get_series_stake_series_mode(request)
    if mode == SERIES_STAKE_SERIES_RANDOM:
        return random.choice(SERIES_STAKE_SERIES_KEYS_POOL)
    return mode


def _series_stake_package_plays_sdacha_with_base(bet_amount, pack_base, splits):
    """
    Пакет = splits × pack_base → играет по = (ставка // пакет) × pack_base, сдача = остаток.
    Для Tiers / spiel / orphelins pack_base = min серии; для Voisins — шаг серии.
    """
    base = max(1, int(pack_base))
    splits = max(1, int(splits))
    unit = splits * base
    b = int(bet_amount)
    n = b // unit
    plays = n * base
    sdacha = b % unit
    return plays, sdacha


def _series_stake_package_plays_sdacha(bet_amount, series_min_po, splits):
    """Как Tiers: пакет = splits × min серии → играет по и сдача."""
    return _series_stake_package_plays_sdacha_with_base(
        bet_amount,
        series_min_po,
        splits,
    )


def _series_stake_tiers_plays_and_sdacha(bet_amount, series_min_po):
    """
    Tiers, 6 сплитов: пакет = 6 × min играет серия (из AR).
    Ставка // пакет = число полных пакетов → играет по = это × min.
    Сдача = остаток от деления ставки на пакет.
    Пример: ставка 160, min 5 → пакет 30 → 160÷30=5 → играет по 25, сдача 10.
    При min=1 совпадает с divmod(ставка, 6).
    """
    return _series_stake_package_plays_sdacha(
        bet_amount,
        series_min_po,
        SERIES_STAKE_TIERS_SPLITS,
    )


def _series_stake_zero_orphelins_threshold(num_max, series_key):
    nmax = int(num_max)
    if series_key == 'zero':
        return nmax * SERIES_STAKE_ZERO_THRESHOLD_NMAX_MUL
    if series_key == 'orphelins':
        return nmax * SERIES_STAKE_ORPHELINS_THRESHOLD_NMAX_MUL
    raise ValueError(series_key)


def _series_stake_zero_orphelins_plays_sdacha(bet_amount, series_min_po, num_max, series_key):
    """
    Порог: max номер × 4 (0-spiel) или × 5 (Orphelins).
    Ставка ≤ порог: одна фаза — как Tiers, но пакет на 4 или 5 вместо 6.
    Ставка > порог: порог считаем пакетами 4/5; остаток — пакетами 3 (spiel) или 4 (orphelins).
    Пример AR 1-100-1, spiel, ставка 500: порог 400 → 400/4 → 100; остаток 100, 100/3 → 33, сдача 1 → 133 и 1.
    """
    if series_key == 'zero':
        primary = SERIES_STAKE_ZERO_PRIMARY_SPLITS
        phase2 = SERIES_STAKE_ZERO_PHASE2_SPLITS
    elif series_key == 'orphelins':
        primary = SERIES_STAKE_ORPHELINS_PRIMARY_SPLITS
        phase2 = SERIES_STAKE_ORPHELINS_PHASE2_SPLITS
    else:
        raise ValueError(series_key)
    smp = max(1, int(series_min_po))
    threshold = _series_stake_zero_orphelins_threshold(num_max, series_key)
    b = int(bet_amount)
    if b <= threshold:
        return _series_stake_package_plays_sdacha(b, smp, primary)
    plays1, rem_after_threshold = _series_stake_package_plays_sdacha(
        threshold, smp, primary
    )
    rest = b - threshold
    plays2, rem_after_rest = _series_stake_package_plays_sdacha(rest, smp, phase2)
    return plays1 + plays2, rem_after_threshold + rem_after_rest


def _series_stake_voisins_threshold(num_max):
    """Порог = номер max × 1.5 × 9; целое: max × 27 // 2."""
    nmax = int(num_max)
    return (nmax * 27) // 2


def _series_stake_voisins_plays_sdacha(bet_amount, series_step, num_max):
    """
    До порога: пакеты по 9 × шаг серии. После порога: остаток пакетами 7 × шаг серии.
    Порог = num_max × 1.5 × 9.
    """
    st = max(1, int(series_step))
    threshold = _series_stake_voisins_threshold(num_max)
    b = int(bet_amount)
    primary = SERIES_STAKE_VOISINS_PRIMARY_SPLITS
    phase2 = SERIES_STAKE_VOISINS_PHASE2_SPLITS
    if b <= threshold:
        return _series_stake_package_plays_sdacha_with_base(b, st, primary)
    plays1, rem_after_threshold = _series_stake_package_plays_sdacha_with_base(
        threshold, st, primary
    )
    rest = b - threshold
    plays2, rem_after_rest = _series_stake_package_plays_sdacha_with_base(
        rest, st, phase2
    )
    return plays1 + plays2, rem_after_threshold + rem_after_rest


def _series_stake_build_task_tiers(stake_params):
    """
    Tiers: случайная ставка из настроек «Ставка» (min, max, сетка step).
    k = целая часть ставки / 6 (для совместимости с сохранением в сессии).
    """
    amount = _pick_random_stake_amount(
        stake_params['stake_min'],
        stake_params['stake_max'],
        stake_params['stake_step'],
    )
    k = amount // SERIES_STAKE_TIERS_SPLITS
    return amount, k


def _series_stake_build_random_stake_for_splits(stake_params, splits):
    """Случайная ставка по настройкам; splits — делитель для вспом. k в сессии."""
    amount = _pick_random_stake_amount(
        stake_params['stake_min'],
        stake_params['stake_max'],
        stake_params['stake_step'],
    )
    k = amount // max(1, int(splits))
    return amount, k


def _series_stake_generate_round(request):
    """Текст задания и сессия раунда; Tiers / spiel / orphelins / Voisins — число ставки и ответы."""
    if _get_series_stake_ar_preset(request) == SERIES_STAKE_AR_RANDOM:
        pick = random.choice(SERIES_STAKE_AR_PRESETS)
        rolled = _parse_series_stake_ar_triple(pick)
        request.session['ar_series_stake_ar_roll_cached'] = rolled
        request.session['ar_series_stake_ar_roll_preset_id'] = pick
    p = _get_series_stake_ar_params(request)
    series_key = _resolve_series_stake_series_key(request)
    request.session['ar_series_stake_series_key'] = series_key
    request.session.pop('ar_series_stake_bet_amount', None)
    request.session.pop('ar_series_stake_tiers_k', None)
    request.session.pop('ar_series_stake_round_series_min_po', None)
    request.session.pop('ar_series_stake_round_num_max', None)
    request.session.pop('ar_series_stake_round_series_step', None)

    if series_key == 'tiers':
        stake_eff = _series_stake_effective_pick_params(request, 'tiers', p)
        amount, k = _series_stake_build_task_tiers(stake_eff)
        request.session['ar_series_stake_bet_amount'] = amount
        request.session['ar_series_stake_tiers_k'] = k
        smp = p['series_min_po']
        request.session['ar_series_stake_round_series_min_po'] = smp
        plays, sdacha = _series_stake_tiers_plays_and_sdacha(amount, smp)
        request.session['ar_series_stake_plays'] = plays
        request.session['ar_series_stake_sdacha'] = sdacha
        text = '%d' % (amount,)
        request.session['ar_series_stake_task'] = text
        request.session['ar_series_stake_round_started_at'] = time.time()
        return text
    if series_key == 'zero':
        stake_eff = _series_stake_effective_pick_params(request, 'zero', p)
        amount, k = _series_stake_build_random_stake_for_splits(
            stake_eff, SERIES_STAKE_ZERO_PRIMARY_SPLITS
        )
        request.session['ar_series_stake_bet_amount'] = amount
        request.session['ar_series_stake_tiers_k'] = k
        request.session['ar_series_stake_round_series_min_po'] = p['series_min_po']
        request.session['ar_series_stake_round_num_max'] = p['num_max']
        plays, sdacha = _series_stake_zero_orphelins_plays_sdacha(
            amount, p['series_min_po'], p['num_max'], 'zero'
        )
        request.session['ar_series_stake_plays'] = plays
        request.session['ar_series_stake_sdacha'] = sdacha
        text = '%d' % (amount,)
        request.session['ar_series_stake_task'] = text
        request.session['ar_series_stake_round_started_at'] = time.time()
        return text
    if series_key == 'orphelins':
        stake_eff = _series_stake_effective_pick_params(request, 'orphelins', p)
        amount, k = _series_stake_build_random_stake_for_splits(
            stake_eff, SERIES_STAKE_ORPHELINS_PRIMARY_SPLITS
        )
        request.session['ar_series_stake_bet_amount'] = amount
        request.session['ar_series_stake_tiers_k'] = k
        request.session['ar_series_stake_round_series_min_po'] = p['series_min_po']
        request.session['ar_series_stake_round_num_max'] = p['num_max']
        plays, sdacha = _series_stake_zero_orphelins_plays_sdacha(
            amount, p['series_min_po'], p['num_max'], 'orphelins'
        )
        request.session['ar_series_stake_plays'] = plays
        request.session['ar_series_stake_sdacha'] = sdacha
        text = '%d' % (amount,)
        request.session['ar_series_stake_task'] = text
        request.session['ar_series_stake_round_started_at'] = time.time()
        return text
    if series_key == 'voisins':
        stake_eff = _series_stake_effective_pick_params(request, 'voisins', p)
        amount, k = _series_stake_build_random_stake_for_splits(
            stake_eff, SERIES_STAKE_VOISINS_PRIMARY_SPLITS
        )
        request.session['ar_series_stake_bet_amount'] = amount
        request.session['ar_series_stake_tiers_k'] = k
        request.session['ar_series_stake_round_series_min_po'] = p['series_min_po']
        request.session['ar_series_stake_round_num_max'] = p['num_max']
        request.session['ar_series_stake_round_series_step'] = p['series_step']
        plays, sdacha = _series_stake_voisins_plays_sdacha(
            amount,
            p['series_step'],
            p['num_max'],
        )
        request.session['ar_series_stake_plays'] = plays
        request.session['ar_series_stake_sdacha'] = sdacha
        text = '%d' % (amount,)
        request.session['ar_series_stake_task'] = text
        request.session['ar_series_stake_round_started_at'] = time.time()
        return text
    request.session.pop('ar_series_stake_plays', None)
    request.session.pop('ar_series_stake_sdacha', None)
    text = SERIES_STAKE_TASK_PLACEHOLDER
    request.session['ar_series_stake_task'] = text
    request.session['ar_series_stake_round_started_at'] = time.time()
    return text


def ar_series_stake(request):
    """Ставка на серию: настройки в модалке; сценарий и проверка — на стороне продукта."""
    if request.method == 'POST' and request.POST.get('action') == 'settings':
        series_mode = request.POST.get('series_mode', '')
        if series_mode in SERIES_STAKE_VALID_SERIES_MODES:
            request.session['ar_series_stake_series_mode'] = series_mode
        preset = request.POST.get('ar_preset', '')
        if preset == SERIES_STAKE_AR_RANDOM:
            request.session['ar_series_stake_ar_preset'] = SERIES_STAKE_AR_RANDOM
            request.session.pop('ar_series_stake_ar_roll_cached', None)
            request.session.pop('ar_series_stake_ar_roll_preset_id', None)
        elif preset == SERIES_STAKE_AR_CUSTOM:
            request.session['ar_series_stake_ar_preset'] = SERIES_STAKE_AR_CUSTOM
            request.session.pop('ar_series_stake_ar_roll_cached', None)
            request.session.pop('ar_series_stake_ar_roll_preset_id', None)
            nm = _clamp_int(request.POST.get('custom_num_min'), 1, 9999, 1)
            xm = _clamp_int(request.POST.get('custom_num_max'), 1, 9999, 100)
            if nm > xm:
                nm, xm = xm, nm
            request.session['ar_series_stake_num_min'] = nm
            request.session['ar_series_stake_num_max'] = xm
            request.session['ar_series_stake_series_min_po'] = _clamp_int(
                request.POST.get('custom_series_min_po'), 1, 9999, 1
            )
            request.session['ar_series_stake_series_step'] = _clamp_int(
                request.POST.get('custom_series_step'), 1, 9999, 1
            )
        elif preset in SERIES_STAKE_AR_PRESETS:
            request.session['ar_series_stake_ar_preset'] = preset
            request.session.pop('ar_series_stake_ar_roll_cached', None)
            request.session.pop('ar_series_stake_ar_roll_preset_id', None)
        p_saved = _get_series_stake_ar_params(request)
        mode_save = _get_series_stake_series_mode(request)
        d_stake = _series_stake_stake_defaults_for_mode(mode_save, p_saved)
        sm = _clamp_int(request.POST.get('stake_min'), 1, 999999, d_stake['stake_min'])
        sx = _clamp_int(request.POST.get('stake_max'), 1, 999999, d_stake['stake_max'])
        ss = _clamp_int(request.POST.get('stake_step'), 1, 999999, d_stake['stake_step'])
        if sm > sx:
            sm, sx = sx, sm
        request.session['ar_series_stake_stake_min'] = sm
        request.session['ar_series_stake_stake_max'] = sx
        request.session['ar_series_stake_stake_step'] = ss
        raw_te = request.POST.get('timer_enabled', '0')
        request.session['ar_series_stake_timer_enabled'] = str(raw_te).strip() in (
            '1',
            'on',
            'true',
            'True',
            'yes',
        )
        request.session['ar_series_stake_timer_seconds'] = _clamp_int(
            request.POST.get('timer_seconds'),
            1,
            SERIES_STAKE_TIMER_SECONDS_MAX,
            SERIES_STAKE_TIMER_DEFAULT_SECONDS,
        )
        return redirect(reverse('ar_series_stake'))

    if request.method == 'GET' or (request.method == 'POST' and request.POST.get('action') == 'next'):
        text = _series_stake_generate_round(request)
        return render(request, 'ar/ar_series_stake.html', _series_stake_template_ctx(request, {
            'task_description': text,
            'message': '',
            'success': None,
            'skipped': False,
            'user_igraet': '',
            'user_sdacha': '',
        }))

    task_description = request.session.get('ar_series_stake_task', '')
    series_key = request.session.get('ar_series_stake_series_key')
    bet_amount = request.session.get('ar_series_stake_bet_amount')
    round_smp = request.session.get('ar_series_stake_round_series_min_po')
    round_nmax = request.session.get('ar_series_stake_round_num_max')
    round_st = request.session.get('ar_series_stake_round_series_step')
    ar_live = _get_series_stake_ar_params(request)
    if round_smp is None and bet_amount is not None:
        round_smp = ar_live['series_min_po']
    if round_nmax is None and bet_amount is not None:
        round_nmax = ar_live['num_max']
    if round_st is None and bet_amount is not None:
        round_st = ar_live['series_step']
    correct_plays = correct_sdacha = None
    if (
        series_key == 'tiers'
        and bet_amount is not None
        and round_smp is not None
    ):
        correct_plays, correct_sdacha = _series_stake_tiers_plays_and_sdacha(
            bet_amount, round_smp
        )
    elif (
        series_key in ('zero', 'orphelins')
        and bet_amount is not None
        and round_smp is not None
        and round_nmax is not None
    ):
        correct_plays, correct_sdacha = _series_stake_zero_orphelins_plays_sdacha(
            bet_amount,
            round_smp,
            round_nmax,
            series_key,
        )
    elif (
        series_key == 'voisins'
        and bet_amount is not None
        and round_nmax is not None
        and round_st is not None
    ):
        correct_plays, correct_sdacha = _series_stake_voisins_plays_sdacha(
            bet_amount,
            round_st,
            round_nmax,
        )
    message = ''
    success = None
    skipped = False
    solve_seconds = None

    if request.POST.get('action') == 'skip':
        supported = ('tiers', 'zero', 'orphelins', 'voisins')
        if (
            series_key in supported
            and correct_plays is not None
            and correct_sdacha is not None
        ):
            message = (
                f'Пропущено. Играет по: {correct_plays}, сдача: {correct_sdacha}'
            )
        else:
            message = 'Пропущено.'
        skipped = True
    elif request.POST.get('action') == 'check':
        if (
            series_key not in ('tiers', 'zero', 'orphelins', 'voisins')
            or correct_plays is None
            or correct_sdacha is None
        ):
            message = 'Для этой серии проверка ещё не настроена.'
            success = False
        else:
            try:
                user_igraet = int(request.POST.get('igraet_po', '').replace(' ', ''))
            except (TypeError, ValueError):
                user_igraet = None
            try:
                user_sdacha = int(request.POST.get('sdacha', '').replace(' ', ''))
            except (TypeError, ValueError):
                user_sdacha = None
            if user_igraet is None or user_sdacha is None:
                message = 'Введите «играет по» и «сдачу»'
                success = False
            elif user_igraet == correct_plays and user_sdacha == correct_sdacha:
                message = 'Правильно!'
                success = True
                t0 = request.session.get('ar_series_stake_round_started_at')
                if t0 is not None:
                    try:
                        solve_seconds = round(
                            max(0.0, time.time() - float(t0)),
                            1,
                        )
                    except (TypeError, ValueError):
                        solve_seconds = None
            else:
                errors = []
                if user_igraet != correct_plays:
                    errors.append(f'играет по {correct_plays}')
                if user_sdacha != correct_sdacha:
                    errors.append(f'сдача {correct_sdacha}')
                message = f'Нет. Правильно: {", ".join(errors)}'
                success = False

    return render(request, 'ar/ar_series_stake.html', _series_stake_template_ctx(request, {
        'task_description': task_description,
        'message': message,
        'success': success,
        'skipped': skipped,
        'user_igraet': request.POST.get('igraet_po', ''),
        'user_sdacha': request.POST.get('sdacha', ''),
        'solve_seconds': solve_seconds,
    }))


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
