from django.shortcuts import render, redirect
from data.cards import get_shuffled_shoe
from blackjack.utils.payout import get_random_bet
from training.utils.timer import process_timer_settings
from .utils.combo import make_combo_queue, make_holdem_combo_queue, hand_to_combo, best_combo_from_7, COMBO_CHOICES, COMBO_CHOICES_HOLDEM
from .utils.payout import check_user_payout


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


def texas_holdem(request):
    shoe = request.session.get('texas_shoe', [])
    if not shoe or request.method == 'GET':
        shoe = get_shuffled_shoe()
        request.session['texas_shoe'] = shoe

    if len(shoe) < 7:
        shoe = get_shuffled_shoe()
        request.session['texas_shoe'] = shoe

    board = [shoe.pop(0) for _ in range(5)]
    hole = [shoe.pop(0) for _ in range(2)]
    request.session['texas_shoe'] = shoe

    return render(request, 'poker/texas_holdem.html', {
        'board': board,
        'hole': hole,
    })


def combo(request):
    queue = request.session.get('combo_queue')
    if not queue or request.method == 'GET' and not request.GET.get('next'):
        queue = make_combo_queue()
        request.session['combo_queue'] = queue

    if request.method == 'POST' and request.POST.get('action') == 'next':
        queue.pop(0)
        request.session['combo_queue'] = queue

    if not queue:
        queue = make_combo_queue()
        request.session['combo_queue'] = queue

    hand = queue[0]
    user_combo = request.POST.get('user_combo')
    message = ''
    success = None
    if request.method == 'POST' and request.POST.get('action') == 'check':
        correct_combo = hand_to_combo(hand)
        if user_combo == correct_combo:
            message = "Верно!"
            success = True
        else:
            message = "Неправильно!"
            success = False

    return render(request, 'poker/combo.html', {
        'hand': hand,
        'combo_choices': COMBO_CHOICES,
        'message': message,
        'success': success,
    })


def combo_holdem(request):
    queue = request.session.get('combo_holdem_queue')
    if not queue or request.method == 'GET' and not request.GET.get('next'):
        queue = make_holdem_combo_queue()
        request.session['combo_holdem_queue'] = queue

    if request.method == 'POST' and request.POST.get('action') == 'next':
        queue.pop(0)
        request.session['combo_holdem_queue'] = queue

    if not queue:
        queue = make_holdem_combo_queue()
        request.session['combo_holdem_queue'] = queue

    hand = queue[0]
    board = hand[:5]
    hole = hand[5:7]
    user_combo = request.POST.get('user_combo')
    message = ''
    success = None
    if request.method == 'POST' and request.POST.get('action') == 'check':
        correct_combo = best_combo_from_7(hand)
        if user_combo == correct_combo:
            message = "Верно!"
            success = True
        else:
            message = "Неправильно!"
            success = False

    return render(request, 'poker/combo_holdem.html', {
        'board': board,
        'hole': hole,
        'hand': hand,
        'combo_choices': COMBO_CHOICES_HOLDEM,
        'message': message,
        'success': success,
    })


def payout_view(request):
    """Oasis Poker: считаем выплату. min/max/step в настройках (шестерёнка), ставка, комбинация, ответ пользователя."""
    min_bet = request.session.get('poker_payout_min_bet', 25)
    max_bet = request.session.get('poker_payout_max_bet', 500)
    step = request.session.get('poker_payout_step', 5)

    if request.method == 'POST' and request.POST.get('action') == 'settings':
        process_timer_settings(request)
        min_bet = _parse_int(request.POST.get('min_bet'), min_bet, 1, 10000)
        max_bet = _parse_int(request.POST.get('max_bet'), max_bet, 1, 10000)
        step = _parse_int(request.POST.get('step'), step, 1, 1000)
        if min_bet >= max_bet:
            max_bet = min_bet + step
        if step > max_bet - min_bet:
            step = max(1, max_bet - min_bet)
        request.session['poker_payout_min_bet'] = min_bet
        request.session['poker_payout_max_bet'] = max_bet
        request.session['poker_payout_step'] = step
        return redirect('poker_payout')

    queue = request.session.get('poker_payout_queue')
    if not queue:
        queue = make_combo_queue()
        request.session['poker_payout_queue'] = queue

    bet = request.session.get('poker_current_bet')
    hand = request.session.get('poker_current_hand')

    if request.method == 'GET' or (request.method == 'POST' and request.POST.get('action') == 'next'):
        if not queue:
            queue = make_combo_queue()
            request.session['poker_payout_queue'] = queue
        hand = queue.pop(0)
        request.session['poker_payout_queue'] = queue
        request.session['poker_current_hand'] = hand
        bet = get_random_bet(min_bet, max_bet, step)
        request.session['poker_current_bet'] = bet
        return render(request, 'poker/payout.html', {
            'bet': bet,
            'hand': hand,
            'combo': hand_to_combo(hand),
            'min_bet': min_bet,
            'max_bet': max_bet,
            'step': step,
            'message': '',
            'success': None,
            'skipped': False,
        })

    message = ''
    success = None
    skipped = False
    action = request.POST.get('action')
    user_payout = request.POST.get('user_payout', '')
    combo = hand_to_combo(hand)

    if action == 'skip':
        _, correct = check_user_payout(0, bet, combo)
        message = f"Пропущено. Правильный ответ: {correct}"
        success = None
        skipped = True
    elif action == 'check':
        is_correct, correct = check_user_payout(user_payout, bet, combo)
        if is_correct:
            message = "Правильно!"
            success = True
        else:
            message = "Неправильно!"
            success = False

    return render(request, 'poker/payout.html', {
        'bet': bet,
        'hand': hand,
        'combo': combo,
        'min_bet': min_bet,
        'max_bet': max_bet,
        'step': step,
        'message': message,
        'success': success,
        'skipped': skipped,
    })


def index(request):
    return render(request, 'poker/index.html')
