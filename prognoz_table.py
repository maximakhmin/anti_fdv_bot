import gspread
import numpy as np
from PROGNOZ import prognoz_func
import requests
from tokens import G_TABLE_KEY

KEY = G_TABLE_KEY
FILE_NAME = "credentials_anti_fdv.json"

def race_parse(week):

    url = f'https://ergast.com/api/f1/current/{week}/results.json'
    request = requests.get(url)
    result = []
    data = request.json()
    pilots = data["MRData"]["RaceTable"]["Races"][0]["Results"]

    for elem in pilots:
        result.append(elem["Driver"]["familyName"])
        if (elem["position"]=="1"):
            poul = elem["Driver"]["familyName"]
    result.append(poul)

    eng_to_ru = {
        'Verstappen': 'Ферстаппен',
        'Pérez': 'Перес',
        'Norris': 'Норрис',
        'Piastri': 'Пиастри',
        'Russell': 'Рассел',
        'Hamilton': 'Хэмильтон',
        'Alonso': 'Алонсо',
        'Stroll': 'Стролл',
        'Albon': 'Албон',
        'Sargeant': 'Сержант',
        'Bottas': 'Боттас',
        'Zhou': 'Чжоу',
        'Tsunoda': 'Цунода',
        'Gasly': 'Гасли',
        'de Vries': 'Деврис',
        'Ocon': 'Окон',
        'Leclerc': 'Леклер',
        'Sainz': 'Сайнс',
        'Hülkenberg': 'Хюлькенберг',
        'Magnussen': 'Магнуссен',
        'Lawson': 'Лоусон'
    }
    return [eng_to_ru.get(surname, surname) for surname in result]

def getLastThree(prognozes):
    result = []
    names = ['', 'Имя']

    for elem in prognozes[::-1]:
        if elem[1] not in names:
            names.append(elem[1])
            result.append(elem[1:])

    return result


def main(RACE):
    try:

        gc = gspread.service_account(FILE_NAME)
        sheet = gc.open_by_key(KEY)

        result = sheet.worksheet("results2023")
        prognoz = sheet.worksheet("prognoz")


        # получение диапазона
        cell_start = result.find(RACE)
        col = cell_start.col+1
        while result.cell(cell_start.row, col).value == None:
            col+=1
        col-=1
        cell_finish = result.cell(cell_start.row+22, col)
        RANGE = cell_start.address+':'+cell_finish.address
        WEEK = result.cell(cell_start.row, cell_start.col-2).value


        # получение прогнозов из опроса
        prognozes = prognoz.get_all_values()
        prognozes = getLastThree(prognozes)


        # получение результата гонки
        RACE_RESULT = race_parse(WEEK)


        # перезапись таблицы
        race = result.get_values(RANGE)

        race = [[race[j][i] for j in range(len(race))] for i in range(len(race[0]))] # транспонирование

        race[0][2:23] = RACE_RESULT

        data = []
        for i in range(1, len(race), 2):
            name = race[i][1]
            for elem in prognozes:
                if elem[0]==name:
                    race[i][2:] = elem[1:11]+['']*10+[elem[-1]]
                    player_prognoz= elem[1:11]
                    player_pole = elem[-1]
            player_result, points = prognoz_func(RACE_RESULT, player_prognoz)
            race[i+1][2:12] = player_result
            temp = 0
            if player_pole==RACE_RESULT[-1]:
                temp = 5
            race[i+1][2:] = player_result+['']*10+[temp]

            data.append([name, points+temp])

        race = [[race[j][i] for j in range(len(race))] for i in range(len(race[0]))] # транспонирование
        result.update(RANGE, race)


        # форматирование вывода
        b = True
        while b:
            b = False
            for i in range(1, len(data)):
                if (data[i-1][1] < data[i][1]):
                    temp = data[i-1]
                    data[i-1] = data[i]
                    data[i] = temp
                    b = True

        return data
    
    except Exception as e:
        return "ERROR"

