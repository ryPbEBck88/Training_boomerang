def dual_hand_value(hand):
    value = [0,0]

    for card in hand:
        value[0] += card['value']
        value[1] = value[0]
        if card['rank'] == 'A':
            value[1] += 10

    return value
# у туза значение надо поменять на 1