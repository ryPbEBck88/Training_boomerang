def update_hand_value(prev_value, card):
    """
    Прибавляет значение карты к прошлому значению руки.
    prev_value: список из двух чисел [v0, v1]
      v0 = сумма, считая все тузы как 1
      v1 = сумма с одним тузом как 11 (остальные тузы как 1)
    card: словарь с ключами 'rank' и 'value'

    Возвращает новый список из двух чисел — новое значение руки после добавления карты.
    """
    if card['rank'] == 'A':
        if prev_value[0] == prev_value[1]:
            # Первый туз: v0+1 (туз как 1), v1+11 (туз как 11)
            return [prev_value[0] + 1, prev_value[1] + 11]
        else:
            # Второй и последующие тузы: оба считаем как 1 (иначе перебор)
            return [prev_value[0] + 1, prev_value[1] + 1]
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

