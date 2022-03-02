import requests

from config import Config
bot_token = Config.BOT_TOKEN
def sendMessage(telegram_id, bot_message:str):
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + str(telegram_id) + '&text=' + str(bot_message)
    response = requests.get(send_text)


     