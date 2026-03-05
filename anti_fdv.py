import telebot
import requests
from datetime import datetime
from datetime import timedelta
import prognoz_table
from tokens import TOKEN, CHAT_ID, FORM_LINK, MARKS
import time
import threading
import pytz


bot = telebot.TeleBot(TOKEN)


def get_next_race_info():
    url = f'https://f1api.dev/api/current/next'
    request = requests.get(url)
    data = request.json()

    url = f"https://f1api.dev/api/drivers/{data['race'][0]['circuit']['fastestLapDriverId']}"
    request = requests.get(url)
    data_fd = request.json()

    dic = {
        'name' : data['race'][0]['raceName'],
        'circuit' : f"{data['race'][0]['circuit']['circuitName']}, {data['race'][0]['circuit']['country']}, {data['race'][0]['circuit']['city']}",
        'lap_record' : f"{data_fd['driver'][0]['name']} {data_fd['driver'][0]['surname']} {data['race'][0]['circuit']['lapRecord']}",
        'qualy_time' : (datetime.strptime(f"{data['race'][0]['schedule']['qualy']['date']} {data['race'][0]['schedule']['qualy']['time']}", "%Y-%m-%d %H:%M:%SZ")).replace(tzinfo=pytz.timezone("UTC")),
        'race_time' : (datetime.strptime(f"{data['race'][0]['schedule']['race']['date']} {data['race'][0]['schedule']['race']['time']}", "%Y-%m-%d %H:%M:%SZ")).replace(tzinfo=pytz.timezone("UTC"))
    }

    return dic


@bot.message_handler(commands=["commands"])
def commands(message):
    mes = "/race : next race info\n/whenrace : next race time\n/whenqualy : next qualy time"
    bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["race"])
def send_race_info(message):
    d = get_next_race_info()
    mes = f"""{d['name']}
{d['circuit']}
Lap record : {d['lap_record']}
Qualy time : {datetime.strftime(d['qualy_time'].astimezone(pytz.timezone("Europe/Moscow")), "%d/%m %H:%M")}
Race time : {datetime.strftime(d['race_time'].astimezone(pytz.timezone("Europe/Moscow")), "%d/%m %H:%M")}""" 
    bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["whenrace"])
def whenrace(message):
    d = get_next_race_info()
    delta = d['race_time'] - datetime.now(pytz.timezone("UTC"))
    mes = f"""Race time : {datetime.strftime(d['race_time'].astimezone(pytz.timezone("Europe/Moscow")), "%d/%m %H:%M")}
Remain : {delta.days} d {int(delta.seconds/3600)} h {int(delta.seconds%3600/60)} m"""
    bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["whenqualy"])
def whenrace(message):
    d = get_next_race_info()
    delta = d['qualy_time'] - datetime.now(pytz.timezone("UTC"))
    mes = f"""Qualye time : {datetime.strftime(d['qualy_time'].astimezone(pytz.timezone("Europe/Moscow")), "%d/%m %H:%M")}
Remain : {delta.days} d {int(delta.seconds/3600)} h {int(delta.seconds%3600/60)} m"""
    bot.send_message(message.chat.id, mes)


def check_time():
    def set_time():
        qualy_time = get_next_race_info()['qualy_time']
        reminds = {timedelta(hours=-24) : "осталось 24 часа",
                   timedelta(hours=-1) : "остался 1 час",
                   timedelta(hours=0) : "прием прогнозов завершен"}
        return qualy_time, reminds
    
    qualy_time, reminds = set_time()
    while True:
        time.sleep(60)
        now = datetime.now(pytz.timezone("UTC"))
        delta = 90 # seconds


        if now > qualy_time:
            qualy_time, reminds = set_time()
            continue
        to_remove = []
        for remind, mes in reminds.items():
            print( now - (qualy_time + remind))
            if abs( ((qualy_time + remind) - now).seconds ) < delta:
                to_remove.append(remind)
                bot.send_message(chat_id=CHAT_ID, text=f"{mes}")
        for rm in to_remove:
            reminds.pop(rm)

        
if __name__ == "__main__":
    t1 = threading.Thread(target=check_time)
    t1.start()
    t2 = threading.Thread(target=bot.infinity_polling(none_stop=True, interval=1))
    t2.start()


# bot.infinity_polling(none_stop=True, interval=1)