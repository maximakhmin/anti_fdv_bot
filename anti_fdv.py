import telebot
import requests
from datetime import datetime
from datetime import timedelta
import prognoz_table
from tokens import TOKEN

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):

    b = True

    print("message: {}, from: {}".format(message.text, message.from_user.username))
    message.text = message.text.lower()

    url = f'https://ergast.com/api/f1/current/next.json?'
    request = requests.get(url)
    data = request.json()
    text = ""
    if "/whenqual" in message.text or "/deadline" in message.text:
        time = data["MRData"]["RaceTable"]["Races"][0]["Qualifying"]
        time = time["date"]+'T'+time["time"][:-1]+".000Z"

        qual = datetime.fromisoformat(time[:-1]) + timedelta(hours=3)
        delta = qual - datetime.now()

        text += "Квала {}".format(qual.strftime('%d/%m/%Y %H:%M'))
        text += "\n\nОсталось {} дней, {} часов, {} минут".format(delta.days, int(delta.seconds/3600), int(delta.seconds%3600/60))

    elif "/whenrace" in message.text:
        time = data["MRData"]["RaceTable"]["Races"][0]
        time = time["date"]+'T'+time["time"][:-1]+".000Z"

        race = datetime.fromisoformat(time[:-1]) + timedelta(hours=3)
        delta = race - datetime.now()

        text += "Гонка {}".format(race.strftime('%d/%m/%Y %H:%M'))
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
    elif "/help" in message.text:
        text = "Команды для бота\n\n/whenrace - время до следующей гонки\n/whenqual /deadline - время для следующей квалификации (дедлайн прогноза)\n/where - где следующая гонка\n/prognoz [Название этапа] - подчет очков прогноза"

    else:
        b = False
        text = ""

    if b:
        bot.send_message(message.chat.id, text)
        

bot.polling(none_stop=True, interval=0)