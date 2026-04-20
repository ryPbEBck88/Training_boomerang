from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from data.cards import get_shuffled_shoe, draw_card
from blackjack.utils.self_draw import update_hand_value, check_action
from .utils.payout import get_random_bet, check_user_payout
from staffroom.services import get_user_wallet
from training.utils.timer import process_timer_settings

STAFF_BJ_MIN_BET = Decimal('10.00')
STAFF_BJ_MAX_BET = Decimal('200.00')
STAFF_BJ_BET_STEP = Decimal('5.00')


def _parse_int(val, default, min_val=None, max_val=None):
    try:
        n = int(float(val))
        if min_val is not None and n < min_val:
            n = min_val
        if max_val is not None and n > max_val:
            n = max_val
        return n
    except (TypeError, ValueError):
        return default


def payout_view(request):
    min_bet = request.session.get('payout_min_bet', 10)
    max_bet = request.session.get('payout_max_bet', 200)
    step = request.session.get('payout_step', 5)

    if request.method == 'POST' and request.POST.get('action') == 'settings':
        process_timer_settings(request)
        min_bet = _parse_int(request.POST.get('min_bet'), min_bet, 1, 10000)
        max_bet = _parse_int(request.POST.get('max_bet'), max_bet, 1, 10000)
        step = _parse_int(request.POST.get('step'), step, 1, 1000)
        if min_bet >= max_bet:
            max_bet = min_bet + step
        if step > max_bet - min_bet:
            step = max(1, max_bet - min_bet)
        request.session['payout_min_bet'] = min_bet
        request.session['payout_max_bet'] = max_bet
        request.session['payout_step'] = step
        return redirect('blackjack_payout')

    bet = request.session.get('current_bet')

    # Новая ставка (GET или "Дальше")
    if request.method == 'GET' or (request.method == 'POST' and request.POST.get('action') == 'next'):
        bet = get_random_bet(min_bet, max_bet, step)
        request.session['current_bet'] = bet
        return render(request, 'blackjack/payout.html', {
            'bet': bet,
            'min_bet': min_bet,
            'max_bet': max_bet,
            'step': step,
            'message': '',
            'show_payout': False,
            'success': None,
            'skipped': False,
        })

    # POST: "Проверить" или "Пропустить"
    message = ''
    show_payout = False
    success = None
    skipped = False

    if request.method == 'POST':
        action = request.POST.get('action')
        user_payout = request.POST.get('user_payout')

        if action == 'skip':
            _, correct = check_user_payout(0, bet)
            message = f"Пропущено. Правильный ответ: {correct}"
            show_payout = True
            success = None
            skipped = True   # <--- вот это добавлено!
        elif action == 'check':
            is_correct, correct = check_user_payout(user_payout, bet)
            if is_correct:
                message = "Правильно!"
                show_payout = True
                success = True
            else:
                message = f"Неправильно!"
                show_payout = True
                success = False

    return render(request, 'blackjack/payout.html', {
        'bet': bet,
        'min_bet': min_bet,
        'max_bet': max_bet,
        'step': step,
        'message': message,
        'show_payout': show_payout,
        'success': success,
        'skipped': skipped,
    })

def self_draw(request):
    timer_seconds = request.session.get('timer_seconds', 3)
    timer_enabled = request.session.get('timer_enabled', False)

    if request.method == 'POST' and request.POST.get('action') == 'settings':
        process_timer_settings(request)
        return redirect('blackjack_self_draw')

    hand = request.session.get('hand', [])
    if request.method == 'GET':
        if request.GET.get('new') or not hand:
            shoe = get_shuffled_shoe(num_decks=6)
            card, shoe = draw_card(shoe)
            hand = [card]
            value = update_hand_value([0, 0], card)
            request.session['shoe'] = shoe
            request.session['hand'] = hand
            request.session['hand_value'] = value
            return render(request, 'blackjack/self_draw.html', {
                'cards': hand,
                'value': value,
                'message': '',
                'game_over': False,
                'timer_seconds': timer_seconds,
                'timer_enabled': timer_enabled,
            })
        value = request.session.get('hand_value', [0, 0])
        return render(request, 'blackjack/self_draw.html', {
            'cards': hand,
            'value': value,
            'message': '',
            'game_over': False,
            'timer_seconds': timer_seconds,
            'timer_enabled': timer_enabled,
        })

    hand = request.session.get('hand', [])
    value = request.session.get('hand_value', [0, 0])
    shoe = request.session.get('shoe', [])
    action = request.POST.get('action')  # 'hit' или 'stand'
    message = ''
    game_over = False

    is_correct, msg = check_action(value, action)
    message = msg if not is_correct else ''
    if not is_correct:
        game_over = True
    else:
        if action == 'hit':
            card, shoe = draw_card(shoe)
            hand.append(card)
            value = update_hand_value(value, card)
        else:
            game_over = True

    request.session['hand'] = hand
    request.session['hand_value'] = value
    request.session['shoe'] = shoe

    success = game_over and is_correct
    context = {
        'cards': hand,
        'value': value,
        'message': message,
        'game_over': game_over,
        'success': success,
        'timer_seconds': timer_seconds,
        'timer_enabled': timer_enabled,
    }
    return render(request, 'blackjack/self_draw.html', context)


def _hand_totals(hand):
    """
    Возвращает:
      low  — сумма, если все тузы считать как 1
      high — "мягкая" сумма с одним тузом как 11 (если возможно), иначе = low
      best — наилучшая не переборная сумма, иначе минимальный перебор
    """
    low = 0
    aces = 0
    for card in hand:
        if card['rank'] == 'A':
            aces += 1
            low += 1
        else:
            low += int(card['value'])

    high = low + 10 if aces > 0 else low

    # Общая "жёсткая" логика: начинаем с тузами как 11, затем по одному
    # переводим их в 1, пока не уйдём из перебора.
    total = low + aces * 10
    soft_aces = aces
    while total > 21 and soft_aces > 0:
        total -= 10
        soft_aces -= 1
    best = total

    return low, high, best


def _format_money(val):
    return f'{val.quantize(Decimal("0.01"))}'


def _double_options(current_bet, wallet_balance):
    """
    Диапазон добавки к ставке на дабл:
    min 10, max = текущая ставка на боксе, шаг 5.
    """
    min_add = Decimal('10.00')
    step = Decimal('5.00')
    # По запросу: дабл доступен до размера текущей ставки включительно,
    # независимо от текущего остатка на балансе.
    max_add = Decimal(current_bet).quantize(Decimal('0.01'))
    if max_add < min_add:
        return []
    options = []
    x = min_add
    while x <= max_add:
        options.append(x.quantize(Decimal('0.01')))
        x += step
    return options


def _parse_bets(request):
    bets = []
    for idx in range(1, 8):
        raw = request.POST.get(f'bet_{idx}', '0').strip()
        if not raw:
            bets.append(Decimal('0.00'))
            continue
        try:
            amount = Decimal(raw)
        except InvalidOperation:
            amount = Decimal('0.00')
        if amount < 0:
            amount = Decimal('0.00')
        bets.append(amount.quantize(Decimal('0.01')))
    return bets


def _is_valid_staff_bet(amount):
    if amount == Decimal('0.00'):
        return True
    if amount < STAFF_BJ_MIN_BET or amount > STAFF_BJ_MAX_BET:
        return False
    return (amount % STAFF_BJ_BET_STEP) == Decimal('0.00')


def _is_ten_value_rank(rank):
    return rank in {'10', 'J', 'Q', 'K'}


def _can_split_pair(hand):
    if len(hand) != 2:
        return False
    r1 = hand[0].get('rank')
    r2 = hand[1].get('rank')
    if not r1 or not r2:
        return False
    return r1 == r2 or (_is_ten_value_rank(r1) and _is_ten_value_rank(r2))


def _split_limit_for_origin(state, origin):
    limits = state.get('split_limits', {})
    if str(origin) in limits:
        return int(limits[str(origin)])
    return 4


def _boxes_for_origin(boxes, origin):
    return [b for b in boxes if int(b.get('origin_box', 0)) == int(origin) and Decimal(b.get('bet', '0')) > 0]


def _can_split_current_box(state, box, wallet_balance):
    if not box or box.get('status') != 'playing':
        return False
    if not _can_split_pair(box.get('hand', [])):
        return False
    bet = Decimal(box.get('bet', '0'))
    if bet <= 0 or wallet_balance < bet:
        return False
    origin = int(box.get('origin_box', 0))
    if origin <= 0:
        return False
    current_count = len(_boxes_for_origin(state.get('boxes', []), origin))
    limit = _split_limit_for_origin(state, origin)
    return current_count < limit


def _display_name_for_box(box):
    origin = int(box.get('origin_box', 0) or 0)
    split_no = box.get('split_no')
    if split_no is None:
        return str(origin) if origin > 0 else '0'
    return f'{origin}.{split_no}'


def _ensure_current_box_ready(state):
    """
    После сплита (не тузов) второй бокс получает вторую карту
    только когда до него реально дошёл ход.
    """
    current_idx = state.get('current_box')
    if current_idx is None:
        return
    boxes = state.get('boxes', [])
    if current_idx < 0 or current_idx >= len(boxes):
        return
    box = boxes[current_idx]
    if box.get('pending_split_draw'):
        card, state['shoe'] = draw_card(state['shoe'])
        box.setdefault('hand', []).append(card)
        box['pending_split_draw'] = False


def _auto_advance_on_twenty_one(state):
    """
    Если текущий бокс уже набрал 21, автоматически закрываем его (stood)
    и переводим ход дальше.
    """
    while True:
        current_idx = state.get('current_box')
        if current_idx is None:
            break
        boxes = state.get('boxes', [])
        if current_idx < 0 or current_idx >= len(boxes):
            break
        box = boxes[current_idx]
        if box.get('status') != 'playing':
            break
        _, _, best = _hand_totals(box.get('hand', []))
        if best != 21:
            break
        box['status'] = 'stood'
        state['current_box'] = _next_active_box_index(state['boxes'], current_idx + 1)
        _ensure_current_box_ready(state)


def _next_active_box_index(boxes, start=0):
    for i in range(start, len(boxes)):
        if Decimal(boxes[i]['bet']) > 0 and boxes[i]['status'] == 'playing':
            return i
    return None


def _dealer_play(state):
    while True:
        _, _, dealer_best = _hand_totals(state['dealer_hand'])
        if dealer_best >= 17:
            break
        card, state['shoe'] = draw_card(state['shoe'])
        state['dealer_hand'].append(card)


def _natural_blackjack_box_indexes(boxes, active_indexes):
    bj_indexes = []
    for idx in active_indexes:
        _, _, best = _hand_totals(boxes[idx]['hand'])
        if len(boxes[idx].get('hand', [])) == 2 and best == 21:
            bj_indexes.append(idx)
    return bj_indexes


def _insurance_eligible_box_indexes(boxes, natural_bj_indexes):
    natural_bj_set = set(natural_bj_indexes or [])
    eligible = []
    for idx, box in enumerate(boxes):
        bet = Decimal(box.get('bet', '0'))
        if bet <= 0:
            continue
        if idx in natural_bj_set:
            continue
        eligible.append(idx)
    return eligible


def _has_live_boxes_for_dealer(state):
    """
    Есть ли боксы, для которых нужен добор/сравнение дилера.
    Не нужны дилеру: bust, surrendered, blackjack_paid, пустые ставки.
    """
    for box in state.get('boxes', []):
        bet = Decimal(box.get('bet', '0'))
        if bet <= 0:
            continue
        if box.get('status') in {'bust', 'surrendered', 'blackjack_paid'}:
            continue
        return True
    return False


def _settle_round(state):
    _, _, dealer_best = _hand_totals(state['dealer_hand'])
    dealer_blackjack = len(state['dealer_hand']) == 2 and dealer_best == 21
    dealer_bust = dealer_best > 21
    total_payout = Decimal('0.00')

    for box in state['boxes']:
        bet = Decimal(box['bet'])
        if bet <= 0:
            box['result'] = 'нет ставки'
            box['payout'] = '0.00'
            continue
        if box.get('status') in {'blackjack_paid', 'surrendered'}:
            # Уже оплачено сразу после раздачи, повторно не считаем.
            continue

        _, _, player_best = _hand_totals(box['hand'])
        player_blackjack = len(box['hand']) == 2 and player_best == 21 and not box.get('is_split_hand')
        player_bust = player_best > 21

        if player_bust:
            payout = Decimal('0.00')
            result = 'проигрыш'
        elif player_best == dealer_best:
            # Ничья по очкам: ставка возвращается (пуш).
            payout = bet
            result = 'пуш'
        elif player_blackjack and dealer_blackjack:
            payout = bet
            result = 'пуш'
        elif player_blackjack:
            payout = (bet * Decimal('2.5')).quantize(Decimal('0.01'))
            result = 'blackjack'
        elif dealer_blackjack:
            # Black Jack дилера (A + 10 за 2 карты) старше обычных 21 у игрока.
            payout = Decimal('0.00')
            result = 'проигрыш'
        elif dealer_bust:
            payout = (bet * Decimal('2.0')).quantize(Decimal('0.01'))
            result = 'выигрыш'
        elif player_best > dealer_best:
            payout = (bet * Decimal('2.0')).quantize(Decimal('0.01'))
            result = 'выигрыш'
        elif player_best == dealer_best:
            payout = bet
            result = 'пуш'
        else:
            payout = Decimal('0.00')
            result = 'проигрыш'

        box['result'] = result
        box['payout'] = _format_money(payout)
        total_payout += payout

    state['total_payout'] = _format_money(total_payout)
    return total_payout


@login_required
def staff_room_blackjack(request):
    wallet = get_user_wallet(request.user)
    state = request.session.get('staff_bj_state')
    message = ''
    payout_anim_enabled = request.session.get('bj_payout_anim_enabled', True)

    if request.method == 'POST' and request.POST.get('action') == 'toggle_payout_anim':
        payout_anim_enabled = request.POST.get('enabled') == '1'
        request.session['bj_payout_anim_enabled'] = payout_anim_enabled
        return redirect('blackjack_staff_room')

    if request.method == 'POST' and request.POST.get('action') == 'new_round':
        bets = _parse_bets(request)
        invalid_bets = [b for b in bets if not _is_valid_staff_bet(b)]
        if invalid_bets:
            message = 'Ставка на бокс: 0 или от 10 до 200, шаг 5.'
            return render(
                request,
                'blackjack/staff_room_blackjack.html',
                {
                    'wallet': wallet,
                    'state': state,
                    'boxes': [],
                    'ordered_boxes': [
                        {
                            'index': idx,
                            'bet': '0.00',
                            'hand': [],
                            'best': None,
                            'score_display': '',
                            'status': 'idle',
                            'result': None,
                            'payout': None,
                            'payout_chip': '0.00',
                            'is_active_bet': False,
                            'is_current': False,
                            'can_surrender': False,
                            'display_name': str(idx),
                            'can_split': False,
                        }
                        for idx in range(7, 0, -1)
                    ],
                    'dealer_best': None,
                    'dealer_is_blackjack': False,
                    'dealer_score_display': None,
                    'message': message,
                    'active_double_options': [],
                    'payout_anim_enabled': payout_anim_enabled,
                },
            )
        total_bet = sum(bets, Decimal('0.00')).quantize(Decimal('0.01'))
        if total_bet <= 0:
            message = 'Укажите ставку хотя бы на один бокс.'
        elif total_bet > wallet.balance:
            message = 'Недостаточно средств на балансе.'
        else:
            with transaction.atomic():
                wallet.balance = (wallet.balance - total_bet).quantize(Decimal('0.01'))
                wallet.save(update_fields=['balance', 'updated_at'])
            shoe = get_shuffled_shoe(num_decks=6)
            boxes = []
            for idx, bet in enumerate(bets, start=1):
                boxes.append(
                    {
                        'bet': _format_money(bet),
                        'hand': [],
                        'status': 'playing',
                        'origin_box': idx,
                        'split_no': None,
                        'is_split_hand': False,
                        'pending_split_draw': False,
                    }
                )
            active_boxes = [idx for idx, bet in enumerate(bets) if bet > 0]

            for idx in active_boxes:
                card, shoe = draw_card(shoe)
                boxes[idx]['hand'].append(card)
            dealer_card, shoe = draw_card(shoe)
            dealer_hand = [dealer_card]
            for idx in active_boxes:
                card, shoe = draw_card(shoe)
                boxes[idx]['hand'].append(card)

            dealer_can_blackjack = dealer_card['rank'] in {'10', 'J', 'Q', 'K', 'A'}
            dealer_upcard_is_ace = dealer_card['rank'] == 'A'
            natural_bj_indexes = _natural_blackjack_box_indexes(boxes, active_boxes)
            instant_blackjack_payout = Decimal('0.00')
            equal_money_offer_boxes = []
            if dealer_upcard_is_ace and natural_bj_indexes:
                equal_money_offer_boxes = natural_bj_indexes
            elif not dealer_can_blackjack:
                for idx in natural_bj_indexes:
                    bet = Decimal(boxes[idx]['bet'])
                    payout = (bet * Decimal('2.5')).quantize(Decimal('0.01'))
                    boxes[idx]['status'] = 'blackjack_paid'
                    boxes[idx]['result'] = 'blackjack'
                    boxes[idx]['payout'] = _format_money(payout)
                    # По требованию: после мгновенной оплаты карты BJ забираются.
                    boxes[idx]['hand'] = []
                    instant_blackjack_payout += payout
            else:
                # При "опасной" карте дилера (10/J/Q/K/A) BJ игрока не требует действий:
                # рука сразу считается завершённой (без мгновенной выплаты, если не Ace equal money).
                for idx in natural_bj_indexes:
                    if boxes[idx].get('status') == 'playing':
                        boxes[idx]['status'] = 'stood'

            if instant_blackjack_payout > 0:
                with transaction.atomic():
                    wallet.balance = (wallet.balance + instant_blackjack_payout).quantize(Decimal('0.01'))
                    wallet.save(update_fields=['balance', 'updated_at'])

            state = {
                'shoe': shoe,
                'dealer_hand': dealer_hand,
                'boxes': boxes,
                'phase': 'equal_money_offer' if equal_money_offer_boxes else 'player_turn',
                'current_box': None if equal_money_offer_boxes else _next_active_box_index(boxes),
                'total_bet': _format_money(total_bet),
                'total_payout': _format_money(instant_blackjack_payout),
                'equal_money_offer_boxes': equal_money_offer_boxes,
                'natural_bj_boxes': natural_bj_indexes,
                'insurance_bet': '0.00',
                'insurance_payout': '0.00',
                'split_limits': {},
                'split_seq': {},
            }
            if state['phase'] == 'player_turn':
                _auto_advance_on_twenty_one(state)
                if state.get('current_box') is None:
                    state['phase'] = 'dealer_turn'
            request.session['staff_bj_state'] = state
            request.session.modified = True
            return redirect('blackjack_staff_room')

    elif request.method == 'POST' and request.POST.get('action') == 'clear_round':
        request.session.pop('staff_bj_state', None)
        return redirect('blackjack_staff_room')

    elif request.method == 'POST' and state and state.get('phase') == 'equal_money_offer':
        action = request.POST.get('action')
        offer_indexes = [int(i) for i in state.get('equal_money_offer_boxes', [])]
        if action in {'equal_money_take', 'equal_money_continue'}:
            if action == 'equal_money_take':
                equal_money_total = Decimal('0.00')
                for idx in offer_indexes:
                    if idx < 0 or idx >= len(state.get('boxes', [])):
                        continue
                    box = state['boxes'][idx]
                    bet = Decimal(box.get('bet', '0'))
                    if bet <= 0:
                        continue
                    payout = (bet * Decimal('2.0')).quantize(Decimal('0.01'))
                    box['status'] = 'blackjack_paid'
                    box['result'] = 'равные деньги'
                    box['payout'] = _format_money(payout)
                    # По требованию: при "равных деньгах" карты BJ забираются.
                    box['hand'] = []
                    equal_money_total += payout
                if equal_money_total > 0:
                    with transaction.atomic():
                        wallet.balance = (wallet.balance + equal_money_total).quantize(Decimal('0.01'))
                        wallet.save(update_fields=['balance', 'updated_at'])
                    current_total = Decimal(state.get('total_payout', '0.00'))
                    state['total_payout'] = _format_money(current_total + equal_money_total)
            else:
                # "Дальше": BJ-боксы остаются на столе и ждут сравнения с дилером.
                for idx in offer_indexes:
                    if idx < 0 or idx >= len(state.get('boxes', [])):
                        continue
                    box = state['boxes'][idx]
                    bet = Decimal(box.get('bet', '0'))
                    if bet > 0 and box.get('status') == 'playing':
                        box['status'] = 'stood'

            state['equal_money_offer_boxes'] = []
            dealer_upcard = state['dealer_hand'][0] if state.get('dealer_hand') else None
            dealer_is_ace = dealer_upcard and dealer_upcard.get('rank') == 'A'
            eligible_insurance_boxes = _insurance_eligible_box_indexes(
                state.get('boxes', []),
                state.get('natural_bj_boxes', []),
            )
            if dealer_is_ace and eligible_insurance_boxes:
                state['phase'] = 'insurance_offer'
                state['insurance_offer_eligible_count'] = len(eligible_insurance_boxes)
                state['insurance_offer_max'] = str(200 * len(eligible_insurance_boxes))
                state['current_box'] = None
            else:
                state['current_box'] = _next_active_box_index(state['boxes'])
                state['phase'] = 'player_turn' if state['current_box'] is not None else 'dealer_turn'
                if state['phase'] == 'player_turn':
                    _ensure_current_box_ready(state)
                    _auto_advance_on_twenty_one(state)
                    if state.get('current_box') is None:
                        state['phase'] = 'dealer_turn'
            request.session['staff_bj_state'] = state
            request.session.modified = True
            return redirect('blackjack_staff_room')

    elif request.method == 'POST' and state and state.get('phase') == 'insurance_offer':
        action = request.POST.get('action')
        if action in {'insurance_take', 'insurance_skip'}:
            eligible_count = int(state.get('insurance_offer_eligible_count') or 0)
            max_insurance = Decimal(str(200 * max(eligible_count, 0))).quantize(Decimal('0.01'))
            if action == 'insurance_take' and max_insurance >= Decimal('1.00'):
                raw_insurance = (request.POST.get('insurance_amount') or '').strip()
                try:
                    insurance_bet = Decimal(raw_insurance).quantize(Decimal('0.01'))
                except Exception:
                    insurance_bet = Decimal('0.00')
                is_whole = insurance_bet == insurance_bet.to_integral_value()
                if not is_whole or insurance_bet < Decimal('1.00') or insurance_bet > max_insurance:
                    message = f'Страхование: сумма от 1 до {int(max_insurance)} (шаг 1).'
                elif insurance_bet > wallet.balance:
                    message = 'Недостаточно средств на страхование.'
                else:
                    with transaction.atomic():
                        wallet.balance = (wallet.balance - insurance_bet).quantize(Decimal('0.01'))
                        wallet.save(update_fields=['balance', 'updated_at'])
                    state['insurance_bet'] = _format_money(insurance_bet)
            else:
                state['insurance_bet'] = '0.00'

            if not message:
                state['insurance_offer_eligible_count'] = 0
                state['insurance_offer_max'] = '0'
                state['current_box'] = _next_active_box_index(state['boxes'])
                state['phase'] = 'player_turn' if state['current_box'] is not None else 'dealer_turn'
                if state['phase'] == 'player_turn':
                    _ensure_current_box_ready(state)
                    _auto_advance_on_twenty_one(state)
                    if state.get('current_box') is None:
                        state['phase'] = 'dealer_turn'
                request.session['staff_bj_state'] = state
                request.session.modified = True
                return redirect('blackjack_staff_room')

    elif request.method == 'POST' and state and state.get('phase') == 'player_turn':
        action = request.POST.get('action')
        current_idx = state.get('current_box')
        if current_idx is not None and action in {'hit', 'stand'}:
            box = state['boxes'][current_idx]
            if action == 'hit':
                card, state['shoe'] = draw_card(state['shoe'])
                box['hand'].append(card)
                _, _, best = _hand_totals(box['hand'])
                if best > 21:
                    box['status'] = 'bust'
                    state['current_box'] = _next_active_box_index(state['boxes'], current_idx + 1)
                    _ensure_current_box_ready(state)
                else:
                    # Остаёмся на текущем боксе, игрок может брать сколько угодно (в т.ч. на 21).
                    state['current_box'] = current_idx
                    _auto_advance_on_twenty_one(state)
            elif action == 'stand':
                box['status'] = 'stood'
                state['current_box'] = _next_active_box_index(state['boxes'], current_idx + 1)
                _ensure_current_box_ready(state)
                _auto_advance_on_twenty_one(state)
            if state['current_box'] is None:
                state['phase'] = 'dealer_turn'
            request.session['staff_bj_state'] = state
            request.session.modified = True
            return redirect('blackjack_staff_room')
        if current_idx is not None and action == 'split':
            box = state['boxes'][current_idx]
            if _can_split_current_box(state, box, wallet.balance):
                old_bet = Decimal(box.get('bet', '0'))
                with transaction.atomic():
                    wallet.balance = (wallet.balance - old_bet).quantize(Decimal('0.01'))
                    wallet.save(update_fields=['balance', 'updated_at'])
                state['total_bet'] = _format_money(Decimal(state.get('total_bet', '0.00')) + old_bet)

                hand = list(box.get('hand', []))
                card_a = hand[0]
                card_b = hand[1]
                origin = int(box.get('origin_box', 0) or 0)
                split_limits = state.get('split_limits', {})
                split_seq = state.get('split_seq', {})
                if str(origin) not in split_seq:
                    split_seq[str(origin)] = 2
                is_ace_split = card_a.get('rank') == 'A' and card_b.get('rank') == 'A'
                if is_ace_split:
                    # Для тузов: максимум 3 бокса по исходному боксу (2 сплита).
                    split_limits[str(origin)] = 3
                elif str(origin) not in split_limits:
                    # Для остальных: максимум 4 бокса (3 сплита).
                    split_limits[str(origin)] = 4

                if box.get('split_no') is None:
                    box['split_no'] = 1
                box['is_split_hand'] = True
                box['hand'] = [card_a]
                box['pending_split_draw'] = False
                card, state['shoe'] = draw_card(state['shoe'])
                box['hand'].append(card)
                if is_ace_split:
                    # После сплита тузов выдаём по одной карте и закрываем бокс.
                    box['status'] = 'stood'

                next_split_no = int(split_seq.get(str(origin), 2))
                new_box = {
                    'bet': _format_money(old_bet),
                    'hand': [card_b],
                    'status': 'stood' if is_ace_split else 'playing',
                    'origin_box': origin,
                    'split_no': next_split_no,
                    'is_split_hand': True,
                    'pending_split_draw': (not is_ace_split),
                }
                split_seq[str(origin)] = next_split_no + 1
                if is_ace_split:
                    card, state['shoe'] = draw_card(state['shoe'])
                    new_box['hand'].append(card)

                state['boxes'].insert(current_idx + 1, new_box)
                state['split_limits'] = split_limits
                state['split_seq'] = split_seq
                state['current_box'] = _next_active_box_index(state['boxes'], current_idx)
                _auto_advance_on_twenty_one(state)
                if state['current_box'] is None:
                    state['phase'] = 'dealer_turn'
                request.session['staff_bj_state'] = state
                request.session.modified = True
                return redirect('blackjack_staff_room')
        if current_idx is not None and action == 'double':
            # Работаем с явной копией текущего бокса, чтобы гарантированно
            # изменять только один индекс и исключить побочные мутации.
            boxes_copy = []
            for b in state['boxes']:
                b_copy = dict(b)
                b_copy['hand'] = list(b.get('hand', []))
                boxes_copy.append(b_copy)
            box = boxes_copy[current_idx]
            if box.get('status') == 'playing' and len(box.get('hand', [])) == 2:
                options = _double_options(Decimal(box.get('bet', '0')), wallet.balance)
                raw = request.POST.get('double_amount', '').strip()
                try:
                    add_amount = Decimal(raw).quantize(Decimal('0.01'))
                except Exception:
                    add_amount = Decimal('0.00')
                if add_amount in options and add_amount > 0:
                    with transaction.atomic():
                        wallet.balance = (wallet.balance - add_amount).quantize(Decimal('0.01'))
                        wallet.save(update_fields=['balance', 'updated_at'])
                    box['bet'] = _format_money(Decimal(box['bet']) + add_amount)
                    state['total_bet'] = _format_money(Decimal(state.get('total_bet', '0.00')) + add_amount)
                    # После дабла даём ровно одну карту и закрываем бокс.
                    card, state['shoe'] = draw_card(state['shoe'])
                    box['hand'].append(card)
                    _, _, best = _hand_totals(box['hand'])
                    box['status'] = 'bust' if best > 21 else 'stood'
                    state['boxes'] = boxes_copy
                    state['current_box'] = _next_active_box_index(state['boxes'], current_idx + 1)
                    _ensure_current_box_ready(state)
                    _auto_advance_on_twenty_one(state)
                    if state['current_box'] is None:
                        state['phase'] = 'dealer_turn'
                    request.session['staff_bj_state'] = state
                    request.session.modified = True
                    return redirect('blackjack_staff_room')
        if current_idx is not None and action == 'surrender':
            box = state['boxes'][current_idx]
            dealer_upcard = state['dealer_hand'][0] if state.get('dealer_hand') else None
            dealer_is_ace = dealer_upcard and dealer_upcard.get('rank') == 'A'
            can_surrender = (
                Decimal(box.get('bet', '0')) > 0
                and box.get('status') == 'playing'
                and len(box.get('hand', [])) == 2
                and not dealer_is_ace
            )
            if can_surrender:
                bet = Decimal(box['bet'])
                payout = (bet / Decimal('2')).quantize(Decimal('0.01'))
                with transaction.atomic():
                    wallet.balance = (wallet.balance + payout).quantize(Decimal('0.01'))
                    wallet.save(update_fields=['balance', 'updated_at'])
                box['status'] = 'surrendered'
                box['result'] = '1/2'
                box['payout'] = _format_money(payout)
                current_total = Decimal(state.get('total_payout', '0.00'))
                state['total_payout'] = _format_money(current_total + payout)
                state['current_box'] = _next_active_box_index(state['boxes'], current_idx + 1)
                _ensure_current_box_ready(state)
                _auto_advance_on_twenty_one(state)
                if state['current_box'] is None:
                    state['phase'] = 'dealer_turn'
                request.session['staff_bj_state'] = state
                request.session.modified = True
                return redirect('blackjack_staff_room')

    if state and state.get('phase') == 'dealer_turn':
        if _has_live_boxes_for_dealer(state):
            _dealer_play(state)
        total_payout = _settle_round(state)
        insurance_bet = Decimal(state.get('insurance_bet', '0.00') or '0.00')
        insurance_payout = Decimal('0.00')
        _, _, dealer_best = _hand_totals(state['dealer_hand'])
        dealer_blackjack = len(state.get('dealer_hand', [])) == 2 and dealer_best == 21
        if insurance_bet > 0 and dealer_blackjack:
            # Страхование 2 к 1: прибыль = 2x, к выдаче = прибыль + возврат ставки страховки.
            insurance_profit = (insurance_bet * Decimal('2.0')).quantize(Decimal('0.01'))
            insurance_payout = (insurance_bet + insurance_profit).quantize(Decimal('0.01'))
        state['insurance_payout'] = _format_money(insurance_payout)
        total_payout = (total_payout + insurance_payout).quantize(Decimal('0.01'))
        state['total_payout'] = _format_money(total_payout)
        with transaction.atomic():
            wallet.balance = (wallet.balance + total_payout).quantize(Decimal('0.01'))
            wallet.save(update_fields=['balance', 'updated_at'])
        state['phase'] = 'settled'
        request.session['staff_bj_state'] = state
        request.session.modified = True

    state = request.session.get('staff_bj_state')
    view_boxes = []
    ordered_boxes = []
    dealer_best = None
    dealer_is_blackjack = False
    dealer_score_display = None
    active_double_options = []
    insurance_offer_max = 0
    insurance_offer_eligible_count = 0
    if state:
        _, _, dealer_best = _hand_totals(state['dealer_hand'])
        dealer_is_blackjack = len(state.get('dealer_hand', [])) == 2 and dealer_best == 21
        if dealer_is_blackjack:
            dealer_score_display = 'BJ'
        elif dealer_best > 21:
            dealer_score_display = 'много'
        else:
            dealer_score_display = str(dealer_best)
        current_box_idx = state.get('current_box')
        if (
            state.get('phase') == 'player_turn'
            and current_box_idx is not None
            and 0 <= current_box_idx < len(state.get('boxes', []))
        ):
            cb = state['boxes'][current_box_idx]
            if cb.get('status') == 'playing' and len(cb.get('hand', [])) == 2:
                active_double_options = [_format_money(v) for v in _double_options(Decimal(cb.get('bet', '0')), wallet.balance)]
        insurance_offer_max = int(state.get('insurance_offer_max') or 0)
        insurance_offer_eligible_count = int(state.get('insurance_offer_eligible_count') or 0)
        for idx, box in enumerate(state['boxes'], start=1):
            low, high, best = _hand_totals(box['hand'])
            player_is_blackjack = len(box.get('hand', [])) == 2 and best == 21
            if player_is_blackjack:
                score_display = 'BJ'
            elif high != low and high <= 21:
                score_display = f'{low} / {high}'
            elif best > 21:
                score_display = 'много'
            else:
                score_display = str(best)

            # Для UI "чипа оплаты" показываем чистую оплату (прибыль), а не возврат ставки:
            # - выигрыш: +ставка
            # - blackjack: +1.5 ставки
            # - пуш: 0
            # - 1/2: возврат половины ставки
            bet_dec = Decimal(box.get('bet', '0') or '0')
            payout_dec = Decimal(box.get('payout', '0') or '0')
            result = box.get('result')
            payout_chip = Decimal('0.00')
            if result == 'выигрыш':
                payout_chip = max(Decimal('0.00'), payout_dec - bet_dec)
            elif result == 'blackjack':
                payout_chip = max(Decimal('0.00'), payout_dec - bet_dec)
            elif result == 'равные деньги':
                payout_chip = max(Decimal('0.00'), payout_dec - bet_dec)
            elif result == '1/2':
                payout_chip = payout_dec
            else:
                payout_chip = Decimal('0.00')
            view_boxes.append(
                {
                    'index': idx,
                    'display_name': _display_name_for_box(box),
                    'bet': box['bet'],
                    'hand': box['hand'],
                    'best': best,
                    'score_display': score_display,
                    'status': box['status'],
                    'result': box.get('result'),
                    'payout': box.get('payout'),
                    'payout_chip': _format_money(payout_chip),
                    'is_active_bet': Decimal(box['bet']) > 0,
                    'is_current': state.get('current_box') == (idx - 1),
                    'can_surrender': (
                        state.get('phase') == 'player_turn'
                        and state.get('current_box') == (idx - 1)
                        and box.get('status') == 'playing'
                        and len(box.get('hand', [])) == 2
                        and state.get('dealer_hand')
                        and state['dealer_hand'][0].get('rank') != 'A'
                    ),
                    'can_split': (
                        state.get('phase') == 'player_turn'
                        and state.get('current_box') == (idx - 1)
                        and _can_split_current_box(state, box, wallet.balance)
                    ),
                }
            )
        ordered_boxes = sorted(view_boxes, key=lambda b: b['index'], reverse=True)
    else:
        ordered_boxes = [
            {
                'index': idx,
                'bet': '0.00',
                'hand': [],
                'best': None,
                'status': 'idle',
                'result': None,
                'payout': None,
                'is_active_bet': False,
                'is_current': False,
                'display_name': str(idx),
                'can_split': False,
            }
            for idx in range(7, 0, -1)
        ]

    return render(
        request,
        'blackjack/staff_room_blackjack.html',
        {
            'wallet': wallet,
            'state': state,
            'boxes': view_boxes,
            'ordered_boxes': ordered_boxes,
            'dealer_best': dealer_best,
            'dealer_is_blackjack': dealer_is_blackjack,
            'dealer_score_display': dealer_score_display,
            'message': message,
            'active_double_options': active_double_options,
            'insurance_offer_max': insurance_offer_max,
            'insurance_offer_eligible_count': insurance_offer_eligible_count,
            'payout_anim_enabled': payout_anim_enabled,
        },
    )


def index(request):
    return render(request, 'blackjack/index.html')