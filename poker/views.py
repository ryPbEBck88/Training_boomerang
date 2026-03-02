from django.shortcuts import render
from data.cards import get_shuffled_shoe
from .utils.combo import make_combo_queue, make_holdem_combo_queue, hand_to_combo, best_combo_from_7, COMBO_CHOICES, COMBO_CHOICES_HOLDEM


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
            message = f"Неправильно! Правильный ответ: {correct_combo}"
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
            message = f"Неправильно! Правильный ответ: {correct_combo}"
            success = False

    return render(request, 'poker/combo_holdem.html', {
        'board': board,
        'hole': hole,
        'hand': hand,
        'combo_choices': COMBO_CHOICES_HOLDEM,
        'message': message,
        'success': success,
    })


def index(request):
    return render(request, 'poker/index.html')
