from django.shortcuts import render
from .utils.combo import make_combo_queue, hand_to_combo, COMBO_CHOICES

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

def index(request):
    return render(request, 'poker/index.html')
