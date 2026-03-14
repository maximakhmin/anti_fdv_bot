import telebot
import requests
from datetime import datetime
from datetime import timedelta
# import prognoz_table
from tokens import TOKEN, CHAT_ID, FORM_LINK, MARKS
import time
import threading
import pytz
from session import load_data, get_f1_session_results


bot = telebot.TeleBot(TOKEN)


def get_next_race_info():
    url = f'https://f1api.dev/api/current/next'
    request = requests.get(url)
    data = request.json()

    is_sprint = False
    if data['race'][0]['schedule']['sprintRace']['date']:
        is_sprint = True

    url = f"https://f1api.dev/api/drivers/{data['race'][0]['circuit']['fastestLapDriverId']}"
    request = requests.get(url)
    data_fd = request.json()

    dic = {
        'is_sprint' : is_sprint,
        'season' : data['season'],
        'round' : data['round'],
        'name' : data['race'][0]['raceName'],
        'circuit_id' : data['race'][0]['circuit']['circuitId'],
        'circuit' : f"{data['race'][0]['circuit']['circuitName']}, {data['race'][0]['circuit']['country']}, {data['race'][0]['circuit']['city']}",
        'lap_record' : f"{data_fd['driver'][0]['name']} {data_fd['driver'][0]['surname']} {data['race'][0]['circuit']['lapRecord']}",
        'qualy_time' : (datetime.strptime(f"{data['race'][0]['schedule']['qualy']['date']} {data['race'][0]['schedule']['qualy']['time']}", "%Y-%m-%d %H:%M:%SZ")).replace(tzinfo=pytz.timezone("UTC")),
        'race_time' : (datetime.strptime(f"{data['race'][0]['schedule']['race']['date']} {data['race'][0]['schedule']['race']['time']}", "%Y-%m-%d %H:%M:%SZ")).replace(tzinfo=pytz.timezone("UTC")),
        'fp1_time' : (datetime.strptime(f"{data['race'][0]['schedule']['fp1']['date']} {data['race'][0]['schedule']['fp1']['time']}", "%Y-%m-%d %H:%M:%SZ")).replace(tzinfo=pytz.timezone("UTC")),
        'fp2_time' : (datetime.strptime(f"{data['race'][0]['schedule']['fp2']['date']} {data['race'][0]['schedule']['fp2']['time']}", "%Y-%m-%d %H:%M:%SZ")).replace(tzinfo=pytz.timezone("UTC")) if not is_sprint else None,
        'fp3_time' : (datetime.strptime(f"{data['race'][0]['schedule']['fp3']['date']} {data['race'][0]['schedule']['fp3']['time']}", "%Y-%m-%d %H:%M:%SZ")).replace(tzinfo=pytz.timezone("UTC")) if not is_sprint else None,
        'sprint_qualy_time' : (datetime.strptime(f"{data['race'][0]['schedule']['sprintQualy']['date']} {data['race'][0]['schedule']['sprintQualy']['time']}", "%Y-%m-%d %H:%M:%SZ")).replace(tzinfo=pytz.timezone("UTC")) if is_sprint else None,
        'sprint_race_time' : (datetime.strptime(f"{data['race'][0]['schedule']['sprintRace']['date']} {data['race'][0]['schedule']['sprintRace']['time']}", "%Y-%m-%d %H:%M:%SZ")).replace(tzinfo=pytz.timezone("UTC")) if is_sprint else None,
    }
    dic['deadline'] = dic['sprint_qualy_time'] if is_sprint else dic['qualy_time']

    return dic

COMMANDS = (
    ('/help', 'Commands'),
    ('/race', 'Next race info'),
    ('/whenrace', 'Next race time'),
    ('/whenqualy', 'Next qualy time'),
    ('/whensprint', 'Sprint info'),
    ('/deadline', 'Next deadline'),
    ('/drivers', 'Current drivers championship standings'),
    ('/constructors', 'Current constructors championship standings'),
    ('/standings', 'Current standings (drivers + constructors)'),
    ('/stats [n=5]', 'Winners and poles for last n races'),
)

@bot.message_handler(commands=["commands", "help"])
def commands(message):
    mes = ""
    for elem in COMMANDS:
        mes += f"{elem[0]} : {elem[1]}\n"
    bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["race"])
def send_race_info(message):
    d = get_next_race_info()
    mes = f"{d['name']}\n"
    mes += f"{d['circuit']}\n\n"
    mes += f"Lap record : {d['lap_record']}\n\n"
    mes += f"Fp1 time : {datetime.strftime(d['fp1_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
    if d['is_sprint']:
        mes += f"\nSprint qualy time : {datetime.strftime(d['sprint_qualy_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
        mes += f"Sprint race time : {datetime.strftime(d['sprint_race_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n\n"
    else:
        mes += f"Fp2 time : {datetime.strftime(d['fp2_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
        mes += f"Fp3 time : {datetime.strftime(d['fp3_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n\n"
    mes += f"Qualy time : {datetime.strftime(d['qualy_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
    mes += f"Race time : {datetime.strftime(d['race_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n\n"
    mes += f"Deadline : {datetime.strftime(d['deadline'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
    bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["whenrace"])
def whenrace(message):
    d = get_next_race_info()
    delta = d['race_time'] - datetime.now(pytz.timezone("UTC"))
    mes = f"Race time : {datetime.strftime(d['race_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
    mes += f"Remain : {delta.days} d {int(delta.seconds/3600)} h {int(delta.seconds%3600/60)} m"
    bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["deadline", "whendeadline"])
def deadline(message):
    d = get_next_race_info()
    delta = d['deadline'] - datetime.now(pytz.timezone("UTC"))
    mes = f"Deadline : {datetime.strftime(d['deadline'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
    mes += f"Remain : {delta.days} d {int(delta.seconds/3600)} h {int(delta.seconds%3600/60)} m"
    bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["whenqualy"])
def whenqualy(message):
    d = get_next_race_info()
    delta = d['qualy_time'] - datetime.now(pytz.timezone("UTC"))
    mes = f"Qualy time : {datetime.strftime(d['qualy_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
    mes += f"Remain : {delta.days} d {int(delta.seconds/3600)} h {int(delta.seconds%3600/60)} m"
    bot.send_message(message.chat.id, mes)

@bot.message_handler(commands=["sprint", "whensprint"])
def whensprint(message):
    d = get_next_race_info()
    if d['is_sprint']:
        delta = d['sprint_qualy_time'] - datetime.now(pytz.timezone("UTC"))
        mes = f"Sprint qualy time : {datetime.strftime(d['sprint_qualy_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
        mes += f"Remain : {delta.days} d {int(delta.seconds/3600)} h {int(delta.seconds%3600/60)} m\n\n"

        delta = d['sprint_race_time'] - datetime.now(pytz.timezone("UTC"))
        mes += f"Sprint race time : {datetime.strftime(d['sprint_race_time'].astimezone(pytz.timezone('Europe/Moscow')), '%d.%m.%Y %H:%M')}\n"
        mes += f"Remain : {delta.days} d {int(delta.seconds/3600)} h {int(delta.seconds%3600/60)} m"
    else:
        mes = "Weekend without sprint"
    bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["drivers"])
def drivers(message):
    url = f'https://f1api.dev/api/current/drivers-championship'
    request = requests.get(url)
    data = request.json()

    mes = "Drivers championship\n\n<pre>"

    for driver in data['drivers_championship']:
        pos = f"{driver['position']}.".ljust(3)
        name = f"{driver['driver']['name']} {driver['driver']['surname']}".ljust(25)
        points = f"{driver['points']}".ljust(4)
        mes += f"{pos} {name} {points}\n"

    mes += "</pre>"

    bot.send_message(message.chat.id, mes, parse_mode="HTML")

@bot.message_handler(commands=["constructors"])
def constructors(message):
    url = f'https://f1api.dev/api/current/constructors-championship'
    request = requests.get(url)
    data = request.json()

    mes = "Constructors championship\n\n<pre>"

    for constructor in data['constructors_championship']:
        pos = f"{constructor['position']}.".ljust(3)
        name = f"{constructor['team']['teamName']}".ljust(25)
        points = f"{constructor['points']}".ljust(4)
        mes += f"{pos} {name} {points}\n"

    mes += "</pre>"

    bot.send_message(message.chat.id, mes, parse_mode="HTML")


@bot.message_handler(commands=["stats", "circuitstats"])
def stats(message):
    count = 0
    try:
        number = int(message.text.split()[1])
    except IndexError or ValueError:
        number = 5
    if number > 10:
        number = 10

    d = get_next_race_info()
    circuit_id = d['circuit_id']
    
    last_year = d['season'] - 1
    race_winners = []
    while len(race_winners)!=number and last_year!=1997:
        url = f'https://f1api.dev/api/{last_year}'
        request = requests.get(url)
        data = request.json()
        for race in data['races']:
            if race['circuit']['circuitId'] == circuit_id:
                race_n = race['round']
                url = f"https://f1api.dev/api/{last_year}/{race_n}/race"
                request = requests.get(url)
                data_race = request.json()
                race_winner_name = f"{data_race['races']['results'][0]['driver']['surname']}"

                url = f"https://f1api.dev/api/{last_year}/{race_n}/qualy"
                request = requests.get(url)
                data_qualy = request.json()
                pole_winner_name = f"{data_qualy['races']['qualyResults'][0]['driver']['surname']}"

                race_winners.append((last_year, pole_winner_name, race_winner_name))
                break
        last_year -= 1
    
    mes = f"Circuit statistics ({d['circuit_id']})\n\n<pre>"
    pos = f"Year".ljust(4)
    pole = f"Pole position".ljust(14)
    winner = f"Winner".ljust(14)
    mes += f"{pos} {pole} {winner}\n"
    for year in race_winners:
        pos = f"{year[0]}".ljust(4)
        pole = f"{year[1]}".ljust(14)
        winner = f"{year[2]}".ljust(14)
        mes += f"{pos} {pole} {winner}\n"

    mes += "</pre>"

    bot.send_message(message.chat.id, mes, parse_mode="HTML")
    

@bot.message_handler(commands=["standings"])
def standings(message):
    drivers(message)
    constructors(message)

def check_time():
    def set_time():
        qualy_time = get_next_race_info()['deadline']
        reminds = {timedelta(hours=-24) : "Осталось 24 часа",
                   timedelta(hours=-2) : "Осталось 2 часа",
                   timedelta(hours=-1) : "Остался 1 час",
                   timedelta(hours=0) : "Прием прогнозов завершен"}
        return qualy_time, reminds
    
    qualy_time, reminds = set_time()
    while True:
        time.sleep(10)
        now = datetime.now(pytz.timezone("UTC"))
        delta = 15 # seconds


        if now > qualy_time:
            qualy_time, reminds = set_time()
            time.sleep(1000)
            continue
        to_remove = []
        for remind, mes in reminds.items():
            d = ((qualy_time + remind) - now)
            if abs( d.days*3600*24 + d.seconds ) < delta:
                to_remove.append(remind)
                bot.send_message(chat_id=CHAT_ID, text=f"{mes}")
        for rm in to_remove:
            reminds.pop(rm)


def send_results():
    def set_time():
        d = get_next_race_info()
        season = d['season']
        round = d['round']
        results = {
            "FP1" : d["fp1_time"] }
        if d["is_sprint"]:
            results["SQ"] = d['sprint_qualy_time']
            results["S"] = d['sprint_race_time']
        else:
            results["FP2"] = d['fp2_time']
            results["FP3"] = d['fp3_time']

        results["Q"] = d["qualy_time"]
        results["R"] = d["race_time"]


        return results, season, round
    
    results, season, round = set_time()
    last_time = results["R"]
    while True:
        now = datetime.now(pytz.timezone("UTC"))

        if len(results)==0 and now > (last_time + timedelta(days=2)):
            last_time = results["R"]
            results, season, round = set_time()
        to_remove = []
        for session, session_t in results.items():
            if session_t < now:
                if (session_t+timedelta(days=1)) < now:
                    to_remove.append(session)
                else:
                    status, mes = get_f1_session_results(season, round, session)
                    if status == 0:
                        bot.send_message(chat_id=CHAT_ID, text=f"{mes}", parse_mode="HTML")
                        to_remove.append(session)
        for rm in to_remove:
            results.pop(rm)

        time.sleep(60)

        
if __name__ == "__main__":
    t1 = threading.Thread(target=check_time)
    t1.start()
    t2 = threading.Thread(target=send_results)
    t2.start()
    t3 = threading.Thread(target=bot.infinity_polling(none_stop=True, interval=1))
    t3.start()



# bot.infinity_polling(none_stop=True, interval=1)

# send_results()
