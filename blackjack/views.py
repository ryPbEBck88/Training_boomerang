from django.shortcuts import render, redirect
from data.cards import get_shuffled_shoe, draw_card
from blackjack.utils.self_draw import update_hand_value, check_action
from .utils.payout import get_random_bet, check_user_payout

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
            })
        value = request.session.get('hand_value', [0, 0])
        return render(request, 'blackjack/self_draw.html', {
            'cards': hand,
            'value': value,
            'message': '',
            'game_over': False,
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
    }
    return render(request, 'blackjack/self_draw.html', context)



def index(request):
    return render(request, 'blackjack/index.html')