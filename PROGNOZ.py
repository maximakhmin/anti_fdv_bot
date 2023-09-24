s1 = """Алонсо
Ферстаппен
Перес
Леклер
Рассел
Хэмильтон
Сайнс
Окон
Гасли
Боттас"""

s1 = s1.split("\n")

race_result ="""Ферстаппен
Хэмильтон
Алонсо
Стролл
Перес
Норрис
Хюлькенберг
Пиастри
Чжоу
Цунода
Боттас
Сайнс
Гасли
Окон
Деврис
Сержант
Магнуссен
Рассел
Албон
Леклер"""

race_result = race_result.split("\n")

def prognoz_func(race_result, player_result):
    points = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    count = 0
    for i in range(len(player_result)):
        if player_result[i] in race_result:
            k = race_result.index(player_result[i])
            count += points[abs(k - i)]
            player_result[i] = (points[abs(k - i)])

    return player_result, count
