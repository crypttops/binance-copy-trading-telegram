import requests

from config import Config
bot_token = Config.BOT_TOKEN
def sendMessage(telegram_id, bot_message:str):
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + str(telegram_id) + '&text=' + str(bot_message)
    response = requests.get(send_text)


def sendAdminMessages(first_name, second_name, utelegram_id, bot_message3):
    bot_message ='*Telegram ID* : ' ''+ str(utelegram_id) +'' ' \n ''  '
    bot_message1='*Name* : ' + first_name + ' ' + second_name + ' \n '' '
    bot_message2 ='*Sir Name* : ' ''+ second_name +' \n '' '
    

    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + '1093054762' + '&parse_mode=Markdown&text=' + bot_message + bot_message1 + bot_message2 +bot_message3
    #https://api.telegram.org/botAAEXuaj6a029wmrNBnOCSFpPadIWga7KOBk/sendMessage?chat_id=1093054762&parse_mode=Markdown&text=atomatedtradingview
    response = requests.get(send_text)