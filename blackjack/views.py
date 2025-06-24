from django.shortcuts import render
from data.cards import get_shuffled_shoe, draw_card
from blackjack.utils.self_draw import update_hand_value, check_action

def self_draw(request):
    if request.method == 'GET' and request.GET.get('new'):
        shoe = get_shuffled_shoe(num_decks=6)
        card, shoe = draw_card(shoe)
        hand = [card]
        value = update_hand_value([0, 0], card)
        request.session['shoe'] = shoe
        request.session['hand'] = hand
        request.session['hand_value'] = value
        context = {
            'cards': hand,
            'value': value,
            'message': '',
            'game_over': False,
        }
        return render(request, 'blackjack/self_draw.html', context)

    hand = request.session.get('hand', [])
    value = request.session.get('hand_value', [0, 0])
    shoe = request.session.get('shoe', [])
    action = request.POST.get('action')  # 'hit' или 'stand'
    message = ''
    game_over = False

    is_correct, message = check_action(value, action)
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

    context = {
        'cards': hand,
        'value': value,
        'message': message,
        'game_over': game_over,
    }
    return render(request, 'blackjack/self_draw.html', context)



def index(request):
    return render(request, 'blackjack/index.html')