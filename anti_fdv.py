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

@bot.message_handler(content_types=['text'])

def get_text_messages(message):

    b = True

    message.text = message.text.lower()

    url = f'https://ergast.com/api/f1/current/next.json?'
    request = requests.get(url)
    data = request.json()
    text = ""
    if "/whenqual" in message.text or "/deadline" in message.text:
        time = data["MRData"]["RaceTable"]["Races"][0]["Qualifying"]
        time = time["date"]+'T'+time["time"][:-1]+".000Z"

        qual = datetime.fromisoformat(time[:-1])
        qual = pytz.timezone('UTC').localize(qual)
        qual = qual.astimezone(pytz.timezone('Europe/Moscow'))
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        delta = qual - now

        text += "Квала {}".format(qual.strftime('%d/%m/%Y %H:%M'))

        if qual > now:
            text += "\n\nОсталось {} дней, {} часов, {} минут".format(delta.days, int(delta.seconds/3600), int(delta.seconds%3600/60))

    elif "/whenrace" in message.text:
        time = data["MRData"]["RaceTable"]["Races"][0]
        time = time["date"]+'T'+time["time"][:-1]+".000Z"

        race = datetime.fromisoformat(time[:-1])
        race = pytz.timezone('UTC').localize(race)
        race = race.astimezone(pytz.timezone('Europe/Moscow'))
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        delta = race - now

        text += "Гонка {}".format(race.strftime('%d/%m/%Y %H:%M'))

        if race > now:
            text += "\n\nОсталось {} дней, {} часов, {} минут".format(delta.days, int(delta.seconds/3600), int(delta.seconds%3600/60))
    elif "/where" in message.text:
        place = data["MRData"]["RaceTable"]["Races"][0]["Circuit"]["circuitName"]
        text += place
    elif "/prognoz" in message.text:
        race = message.text[9:].capitalize()
        data = prognoz_table.main(race)
        if data=="ERROR":
            text+="Ошибка, попробуйте позднее"
        else:
            text+="Прогноз посчитан\n\nРезультаты\n"
            for i in range(len(data)):
                text+="\n{}. {}, {} очков".format(i+1, data[i][0], data[i][1])
    elif "/sprintprognoz" in message.text:
        race = message.text[15:].capitalize()
        data = prognoz_table.main(race, True)
        if data=="ERROR":
            text+="Ошибка, попробуйте позднее"
        else:
            text+="Прогноз посчитан\n\nРезультаты\n"
            for i in range(len(data)):
                text+="\n{}. {}, {} очков".format(i+1, data[i][0], data[i][1])
    elif "/help" in message.text:
        text = "Команды для бота\n\n/whenrace - время до следующей гонки\n/whenqual /deadline - время до следующей квалификации (дедлайн прогноза)\n/where - где следующая гонка\n/prognoz [Название этапа] - подчет очков прогноза\n/sprintprognoz [Название этапа] - подчет очков прогноза вместе со спринтом"

    else:
        b = False
        text = ""

    if b:
        bot.send_message(message.chat.id, text)

class Reminds():
    def __init__(self):
        self.remind1 = ""
        self.remind2 = ""

    def get_reminds(self):
        url = f'https://ergast.com/api/f1/current/next.json?'
        request = requests.get(url)
        data = request.json()

        time = data["MRData"]["RaceTable"]["Races"][0]["Qualifying"]
        time = time["date"]+'T'+time["time"][:-1]+".000Z"
        qual = datetime.fromisoformat(time[:-1])
        qual = pytz.timezone('UTC').localize(qual)
        qual = qual.astimezone(pytz.timezone('Europe/Moscow'))

        self.remind1 = qual - timedelta(days=1)
        self.remind2 = qual - timedelta(hours=1)
        # self.remind1 = datetime(2023, 10, 1, 15, 10, 00)
        # self.remind2 = datetime(2023, 10, 1, 15, 15, 00)
    
    def min_remind1(self):
        self.remind1 -= timedelta(hours=1)
    def min_remind2(self):
        self.remind2 -= timedelta(hours=1)

def check_time():
    reminds = Reminds()
    reminds.get_reminds()
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        delta = timedelta(seconds=60)

        if now - reminds.remind1 < delta and now > reminds.remind1:
            bot.send_message(chat_id=CHAT_ID, text="{}\n\nДелаем прогноз\n\nДедлайн через 24 часа\n\n{}".format(MARKS, FORM_LINK))
            reminds.min_remind1()            
        if now - reminds.remind2 < delta and now > reminds.remind2:
            bot.send_message(chat_id=CHAT_ID, text="{}\n\nОстался 1 час\n\n{}".format(MARKS, FORM_LINK))
            reminds.min_remind2()
        if now - reminds.remind2 > timedelta(days=4) and now > reminds.remind2:
            reminds.get_reminds()
        time.sleep(60)

if __name__ == "__main__":
    t1 = threading.Thread(target=check_time)
    t1.start()
    t2 = threading.Thread(target=bot.infinity_polling(none_stop=True, interval=1))
    t2.start()