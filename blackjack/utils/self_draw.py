def update_hand_value(prev_value, card):
    """
    Прибавляет значение карты к прошлому значению руки.
    prev_value: список из двух чисел [сумма_без_туза, сумма_с_одним_тузом_как_11]
    card: словарь с ключами 'rank' и 'value'

    Возвращает новый список из двух чисел — новое значение руки после добавления карты.
    """

    if card['rank'] == 'A' and prev_value[0] == prev_value[1]:
        return [prev_value[0] + 1, prev_value[1] + 11]
    else:
        return [prev_value[0] + card['value'], prev_value[1] + card['value']]


def get_correct_action(prev_value):
    v0, v1 = prev_value
    if v0 >= 17 or (17 <= v1 <= 21):
        return 'stand'
    else:
        return 'hit'

def check_action(prev_value, user_action):
    """
    Сравнивает действие пользователя с верным действием по правилам.
    prev_value: [v0, v1]
    user_action: строка 'hit' или 'stand'
    Возвращает True/False — правильный ли ход.
    """
    correct = get_correct_action(prev_value)
    if user_action == correct:
        return True, "Верно!"
    else:
        return False, f"Ошибка: надо было выбрать {('Взять карту' if correct == 'hit' else 'Стоп')}"

