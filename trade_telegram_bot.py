# ################################################################

from datetime import datetime, timedelta
from telegram import LabeledPrice, ShippingOption
from backend.operations.binance import getAllOpenOrderSymbol, getAllOpenOrders, getAllOpenPositions
from backend.operations.bot import sendAdminMessages
from backend.operations.db import checkSubscriptionStatus, dbupdate
from backend.utils.binance.client import Client as BinanceSpotClient
from backend.utils import security
from backend.models import  BotConfigsModel
from config import Config
from db import db
from app import app

import json
###################################################################
import logging
from multiprocessing import Process, Pipe
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
    PreCheckoutQueryHandler
)
########################################################################
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# State definitions for top level conversation
SELECTING_ACTION, ADDING_MEMBER, ADDING_SELF, DESCRIBING_SELF = map(chr, range(4))
# State definitions for second level conversation
SELECTING_LEVEL, SELECTING_GENDER, SELECTING_TRADE = map(chr, range(4, 7))
# State definitions for descriptions conversation
SELECTING_FEATURE, SELECTING_FEATURE1, SELECTING_FEATURE2, SELECTING_FEATURE3,SELECTING_FEATURE4, TYPING, TYPING1, TYPING2, TYPING3 = map(chr, range(7, 16))
# Meta states
STOPPING, SHOWING = map(chr, range(16, 18))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END


# own settings 

ENDMANUAL =  map(chr, range(18, 19))
# Different constants for this example
(
    PARENTS,
    CHILDREN,
    NEIGHBORS,
    FOREIGNERS,
    SELF,
    GENDER,
    MALE,
    FEMALE,
    AUTOMATED,
    COPYTRADE,
    SETTINGS,
    SHOW_SETTINGS,
    WEBHOOK,
    WEBHOOKR,
    AGE,
    NAME,
    SUBSCRIPTIONS,
    BUYETH,
    BUYEOS,
    BUYXRP,
    SELLETH,
    SELLEOS,
    SELLXRP,
    LEVERAGE,
    CLOSE,
    POSITION,
    START_OVER,
    FEATURES,
    CURRENT_FEATURE,
    CURRENT_LEVEL,
    TAKEPROFIT, 
    STOPLOSS,
    AMOUNTSETTING,
    TRAILINGSTOP,
    NEWTRAILINGACTIVE,
    LEVERAGESETTING,
    CSUBSCRIPTION,
    CONNECT,
    DISCONNECT
    
) = map(chr, range(19, 58))


global telegram_id
global first_name
global second_name

telegram_id = ''
first_name = ''
second_name  = ''

bot_token =Config.BOT_TOKEN

update1 = {}
print("------------UPDATE 1- INIT----------------", update1)
callback1 = {}
print("------------CALLBACK 1---INIT--------------", callback1)


# return all the user details to avoid crushes in multisking
def getUserDetails(update: Update, context: CallbackContext) -> None:
    if update.callback_query == None:
        user = update.message.from_user
        print(user)
        global telegram_id, first_name
        telegram_id = user.id
        first_name = user.first_name
        second_name = user.last_name
    if update.callback_query != None:
        print("update---------------------------------------", update)
        user = update.callback_query.message.chat
        print('-------------------------------', user)
        telegram_id = user.id
        first_name = user.first_name
        second_name = user.last_name
        print('first name...............',first_name)

    if first_name == 'None' or first_name == None:
        first_name = ''
    if second_name == 'None' or second_name == None:
        second_name = ''
    return user, telegram_id, first_name, second_name


# Top level contversation callbacks
def start(update: Update, context: CallbackContext) -> None:
    global update1
    global callback1
   
    update1 = update
    callback1 = CallbackContext

    print('update1',update1)
    print('callback1', callback1)
    adm_message="Started the bot"
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    # sending starting bot message
    sendAdminMessages(first_name, second_name,telegram_id,adm_message)

    logger.info("User %s started the conversation.", first_name)
    print('telegram id------ ', telegram_id)
    """Select an action: Adding parent/child or show data."""
    text = (
        'Ensure you have been validated using your Binance API Key and Secret'
        
    )
    buttons = [
        [
            InlineKeyboardButton(text='Select Exchange', callback_data=str(ADDING_MEMBER)),
            # InlineKeyboardButton(text='Show data', callback_data=str(SHOWING)),
            InlineKeyboardButton(text='Done', callback_data=str(END))
    ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need do send a new message
    if context.user_data.get(START_OVER):

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        # update1.message.reply_text(text=text, reply_markup=keyboard)
    else:
       
        update.message.reply_text(
            'Hello, Welcome to Binance premium trading bot. If you do not have a binance account use the the link below to open account with binance\n'
            'https://accounts.binance.me/en/register?ref=29337156\n\n'
            'After opening an account with binance use the link below to create your api key and secret \n'
            'https://www.binance.com/en/my/settings/api-management\n\n'
            'On the same window where there is Api key and secret are generated, look for Edit button and click it,then look for an option✅ to enable futures option and click it by ticking the box on top and click SAVE.\n\n'
            'If you do not save you wont be able to trade\n\n'
            'REMEMBER TO TRANFER YOUR DEPOSIT FROM EITHER FUNDING OR SPOT ACCOUNT TO FUTURE ACCOUNT\n\n'
            'After copying the API key and secret click select Exchange, Binance Futures then APi Data buttons, capture the keys on the Api key and Api secret buttons on the bot then click Done\n\n'
            'Click Trading Signals, subscriptions select free plan and the proceed to set Amount and Leverage\n\n'
            'WAIT FOR PROFITABLE SIGNALS TO DO THE MAGIC\n\n'
            'TO CONNECT OR DISCONNECT THE BOT FROM EXECUTING THE ORDERS, Navigate through the trading signals button to access the connect and disconnect buttons'

            
            
        )
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_ACTION


def adding_self(update: Update, context: CallbackContext) -> None:
    
    context.user_data[CURRENT_LEVEL] = SELF
    text = 'By verifying your API keys you accept you are using this bot at your own risk!'
    button = InlineKeyboardButton(text='API DATA', callback_data=str(MALE))
    keyboard = InlineKeyboardMarkup.from_button(button)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return DESCRIBING_SELF

      
def verifyApiData(update: Update, context: CallbackContext, level, user_data):
    key = ''
    text = 'Null'
    text_except = ''
    text_if1 = ''
    text_if2 = ''
    buy = ''
    sell = ''
    secret = ''
    bot_token =Config.BOT_TOKEN
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    vvery12 = telegram_id
    for person in user_data[level]:
        # people = user_data.get(level)
        #the below code doesn't execute settings, just bad naming. It executes BTC Orders
        if person[GENDER] == MALE: #Executes Binance Trading. I suppose this has changed to TRADE BTC
            # gender = female 
            text += f"\nName: {person.get(NAME, '-')}, Age: {person.get(AGE, '-')}"

            api_key =f"{person.get(NAME, '-')}"
            api_secret = f"{person.get(AGE, '-')}"
            
            
            bsclient = BinanceSpotClient(api_key=api_key, api_secret=api_secret)
           
            
            try:
                account_balance = bsclient.get_asset_balance("BTC")
                print("account balance", account_balance)
                with app.app_context():
                    print("here-------------------------------------------------------")
                    exists = bool(db.session.query(BotConfigsModel).filter_by(telegram_id = str(telegram_id)).first())
                    print("existance", exists)
                    if exists:
                        db.session.query(BotConfigsModel).filter_by(telegram_id=str(telegram_id)).update({"key":api_key, "secret":api_secret})
                        db.session.commit()
                        print('Telegram Data Updated')

                        text1 =' Your New Data has been updated \n '
                        

                        text2 = ' Your Binance data has been Verified too. You can proceed and start trading \n'
                        
                        
                        text3 ='Binance ID is valid \n \n'
                        'You can proceed to swap trading'
                        
                        # update.callback_query.edit_message_text(text=(text1 + text2 + text3))

                        # update.callback_query.edit_message_text(text='Type /stop to restart bot and start Trading')

                        textp = text1 + text2 + text3
                        
                        vvery12 = telegram_id
                        bot_message = 'Telegram ID ' ''+ str(vvery12) +'' ' \n \n '
                        ' Name ' + first_name + ' ' + second_name + '\n \n'
                        'Sir Name ' ''+ second_name +'' ' \n \n '
                        ' *User has updated their API key and Secret* '  '\n \n'

                        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + '1093054762' + '&parse_mode=Markdown&text=' + bot_message
                        #https://api.telegram.org/botAAEXuaj6a029wmrNBnOCSFpPadIWga7KOBk/sendMessage?chat_id=1093054762&parse_mode=Markdown&text=atomatedtradingview
                        # response = requests.get(send_text)
                        adm_message = "Updated their API key and Secret successfully"
                        user, telegram_id, first_name, second_name = getUserDetails(update, context)
                        sendAdminMessages(first_name, second_name,telegram_id,adm_message)
                    
                        # send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + str(telegram_id) + '&parse_mode=Markdown&text=' + bot_message
                        # response = requests.get(send_text)

                        # select_level(update, context)   
                        # text_if1  = text1 + text2 + text3
                    
                    else:
                        print("am executing the false function @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
                        todo = BotConfigsModel.create(telegram_id=telegram_id,key=api_key,secret=api_secret)
                        db.session.commit()
                        print('Telegram Table Create Result')
                        print(todo)
                        print('__________________________________________________________')

                        text1 = 'Your data has been captured \n'

                        text2 = 'Your Binance data has been Verified. You can proceed and start trading \n'
                                                    
                        text3 = 'Binance ID is valid, you can proceed to trading \n'
                        
                        # update.callback_query.edit_message_text(text=(text1 + text2 + text3))

                        # update.callback_query.edit_message_text(text='Type /stop to restart bot and Verify your keys afresh')

                        textp = text1 + text2 + text3

                        bot_message = 'Telegram ID ' ''+ str(vvery12) +'' ' \n \n '
                        ' Name ' + first_name + ' ' + second_name + '\n \n'
                        'Sir Name ' ''+ second_name +'' ' \n \n '
                        ' *User has Captured and Validated their API key and Secret for the first time* '  '\n \n'

                        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + '1093054762' + '&parse_mode=Markdown&text=' + bot_message
                        #https://api.telegram.org/botAAEXuaj6a029wmrNBnOCSFpPadIWga7KOBk/sendMessage?chat_id=1093054762&parse_mode=Markdown&text=atomatedtradingview
                        # response = requests.get(send_text)        
                        adm_message = "*User has Captured and Validated their API key and Secret for the first time*"
                        user, telegram_id, first_name, second_name = getUserDetails(update, context)
                        sendAdminMessages(first_name, second_name,telegram_id,adm_message)
                    

               


            except:
                text1 = ' Your Binance API Data is incorrect. Confirm they are correct. \n'

                text2 = 'Visit https://www.binance.com/en/my/settings/api-management to get keys \n'
                
                text3 = 'please verify your Binance keys before proceeding to trade.\n'
                textp = text1 + text2 + text3
                adm_message = "Added incorrect keys"
                user, telegram_id, first_name, second_name = getUserDetails(update, context)
                sendAdminMessages(first_name, second_name,telegram_id,adm_message)

            return textp


def swapTrade(update: Update, context: CallbackContext, level, user_data):
    key = ''
    text = 'Null'
    text_except = ''
    text_if1 = ''
    text_if2 = ''
    buy = ''
    sell = ''
    secret = ''
    bot_token =Config.BOT_TOKEN
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    vvery12 = telegram_id
    for person in user_data[level]:
        # people = user_data.get(level)
        #the below code doesn't execute settings, just bad naming. It executes BTC Orders
        if person[GENDER] == FEMALE: #Executes Binance Trading. I suppose this has changed to TRADE BTC
            # gender = female 
        

            swap_payload =f"{person.get(NAME, '-')}"
            print(swap_payload)
            if swap_payload == "":
                textp = "Invalid message"

            else:
                try:
                    json.loads(swap_payload)
                    with app.app_context():
                        bclient = dbOperations.getBinaceClient(str(telegram_id))
                    textp = binaceSwapOperations.performSwap(bclient, json.loads(swap_payload))
                except:
                    textp = "Invalid Swap message format"
           

    return textp


def handleTradingSignals(user_data, level):
        people = user_data.get(level)
        text=''
        if not people:
            return '\nNo information yet.'

        if level == SELF:
            for person in user_data[level]:
                text += f"\nName: {person.get(NAME, '-')}, Age: {person.get(AGE, '-')}"
        if level == CHILDREN:
            for person in user_data[level]:
                if person[GENDER] == COPYTRADE:
                    person.get(NAME, None), 
                    person.get(AGE, None)
                    
                    return text
            

        
def show_data(update: Update, context: CallbackContext) -> str:
    """Pretty print gathered data."""
    """Pretty print gathered data."""
    print("The execution is still on show data")
    textp = "djhsofddu"
   
    bot_token =Config.BOT_TOKEN
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    user_data = context.user_data
    bot_chatID = str(telegram_id)
   
    user_data = context.user_data
    
    print(user_data, "USER DATA")
    #text = 'Yourself:' + prettyprint(user_data, SELF)
    # print(' prettyprint(user_data, PARENTS)' ,prettyprint(user_data, PARENTS))
    print('PARENTS DATA')
    print('parents data here')
    print(PARENTS)
    level = context.user_data[CURRENT_LEVEL]
    print("the level", level)

    if level == SELF:
        textp = verifyApiData(update, context, level, user_data)
        user_data.clear()
        user_data[START_OVER] = True
        print("------------CALLBACK 1---END START--------------", callback1)
        print("------------UPDATE 1- END START----------------", update1)
        buttons = [[InlineKeyboardButton(text='Back', callback_data=str(END))]]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)  
        return SHOWING

    if level==CHILDREN:
        people = user_data.get(level)
        for person in user_data[level]:
            if person[GENDER] == MALE:  
                textp = verifyApiData(update, context, level, user_data)
                user_data.clear()
                user_data[START_OVER] = True
                print("------------CALLBACK 1---END START--------------", callback1)
                print("------------UPDATE 1- END START----------------", update1)
                # buttons = [[InlineKeyboardButton(text='Back', callback_data=str(END))]]
                # keyboard = InlineKeyboardMarkup(buttons)
                # update.callback_query.answer()
                # update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)  
            if person[GENDER]==COPYTRADE:
                amount = person.get(AGE, None)
                leverage =person.get(LEVERAGE, None)
                
                with app.app_context():
                    status, subscription_type =checkSubscriptionStatus(telegram_id)
                    if status==False:
                        textp = "Update declined, You have no active subscription"
                    else:
                        textp=''
                        if amount is not None:
                            try:
                                float(amount)
                                dbupdate(telegram_id,{'amount':amount})
                                textp+="Amount updated successifully\n"
                                
                            except Exception as e:
                                textp += "Invalid amount, try again\n"
                        if leverage is not None:
                            try:
                                int(leverage)
                                dbupdate(telegram_id,{'leverage':leverage})
                                textp+="Leverage updated successifully\n"
                            except Exception as e:
                                textp += "Invalid leverage, try again\n"
                        if textp=='':
                            textp="No Entry provided"
                adm_message = textp
                user, telegram_id, first_name, second_name = getUserDetails(update, context)
                sendAdminMessages(first_name, second_name,telegram_id,adm_message)


        buttons = [[InlineKeyboardButton(text='Back', callback_data=str(END))]]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)
        textp=''  
        
                
        return SHOWING
    else:
        print("The level", level)
        select_level(update, context)

    
    


def stop(update: Update, context: CallbackContext) -> None:
    """End Conversation by command."""
    update.message.reply_text('Okay, bye.')
    update.message.reply_text('Type, /start to restart bot.')
    adm_message = "Stopped the bot"
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    sendAdminMessages(first_name, second_name,telegram_id,adm_message)

    context.user_data[START_OVER] = False
    return END


def end(update: Update, context: CallbackContext) -> None:
    """End conversation from InlineKeyboardButton."""
    update.callback_query.answer()

    text = 'See you around!'
    update.callback_query.edit_message_text(text=text)
    update.callback_query.edit_message_text(text = 'Type, /start to restart bot.')
    # update.message.reply_text('Type, /start to restart bot.')

    return END


# def select_gender(update: Update, context: CallbackContext) -> None:
#     update1 = update
#     callback1 = CallbackContext
#     """Choose to add mother or father."""
#     level = update.callback_query.data
#     context.user_data[CURRENT_LEVEL] = level

#     text = 'Please select a option to continue'

#     if level == PARENTS or level == CHILDREN or level == SELF or level == NEIGHBORS or level == FOREIGNERS: 

#         buttons = [
#             # [
#             #     InlineKeyboardButton(text= male, callback_data=str(MALE)),
#             # ],
#             [
#                 InlineKeyboardButton(text= female, callback_data=str(FEMALE)),
#                 InlineKeyboardButton(text= automated, callback_data=str(AUTOMATED)),

#             ],
#             [
#                 InlineKeyboardButton(text= settings, callback_data=str(SETTINGS)),
#                 # InlineKeyboardButton(text= show_settings, callback_data=str(SHOW_SETTINGS)),
#             ],
#             [
#                 # InlineKeyboardButton(text='Show data', callback_data=str(SHOWING)),
#                 InlineKeyboardButton(text='Back', callback_data=str(END)),
#             ],
#         ]
#         keyboard = InlineKeyboardMarkup(buttons)
#         update.callback_query.answer()
#         update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
#     return SELECTING_GENDER

def _name_switcher(level):
    if level == PARENTS:
        return 'API DATA', 'Manual Trading', 'Automated Trading','Trading Signals'
    if level == CHILDREN:
        return 'API DATA', 'Manual Trading', 'Automated Trading', 'Trading Signals'


def select_gender(update: Update, context: CallbackContext) -> None:
    """Choose to add mother or father."""
    level = update.callback_query.data
    context.user_data[CURRENT_LEVEL] = level

    text = 'Please select a option to continue'
  
    male, female, automated, copy_trade = _name_switcher(level)
 

   
    buttons = [
        [
            InlineKeyboardButton(text= male, callback_data=str(MALE)),
        ],
        # [
        #     InlineKeyboardButton(text= female, callback_data=str(FEMALE)),
        #     InlineKeyboardButton(text= automated, callback_data=str(AUTOMATED)),

        # ],
        [
             InlineKeyboardButton(text= copy_trade, callback_data=str(COPYTRADE)),
        ],
        [
            InlineKeyboardButton(text='Back', callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    return SELECTING_GENDER
# Second level conversation callbacks
# Second level conversation callbacks
def select_level(update: Update, context: CallbackContext) -> None:
    """Choose to add a parent or a child."""
    text = 'You can perform sell, buy operations or automated trades. To proceed select an option'
    buttons = [
        [
            # InlineKeyboardButton(text='Binance Spot', callback_data=str(PARENTS)),
            InlineKeyboardButton(text='Binance Futures', callback_data=str(CHILDREN)),
        ],
        [
            InlineKeyboardButton(text='Back', callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_LEVEL


def get_all_swaps(update: Update, context: CallbackContext) -> None:
    update1 = update
    callback1 = CallbackContext
    """Cselect_genderhoose to add mother or father."""
    level = update.callback_query.data
    context.user_data[CURRENT_LEVEL] = level

    text = 'Please select a option to continue'
    # all the swap operations here 
    user, telegram_id, first_name, second_name = getUserDetails(update, context)

    # with app.app_context():
    #     bcient =dbOperations.getBinaceClient(str(telegram_id))
    #     all_swaps = binaceSwapOperations.getAllSWaps(bcient)
    #     print(all_swaps)

    #     text = all_swaps[:10]
    #     text = json.dumps(text, indent=2)



    buttons = [
            # [
            #     InlineKeyboardButton(text= male, callback_data=str(MALE)),
            # ],
            [
                InlineKeyboardButton(text= " Manual Swap", callback_data=str(FEMALE)),
                InlineKeyboardButton(text= "Automated Swaps", callback_data=str(AUTOMATED))
                

            ],
           
        ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)         


    return SELECTING_GENDER


def request_swap(update: Update, context: CallbackContext) -> None:
    update1 = update
    callback1 = CallbackContext
    """Cselect_genderhoose to add mother or father."""
    level = update.callback_query.data
    context.user_data[CURRENT_LEVEL] = level

    text = 'Please select a option to continue'
    # all the swap operations here 
   

    buttons = [
        
        [
            # InlineKeyboardButton(text='Show data', callback_data=str(SHOWING)),
            InlineKeyboardButton(text='Back', callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text="request swap", reply_markup=keyboard)

    return SELECTING_GENDER


def perform_swap(update: Update, context: CallbackContext) -> None:
    update1 = update
    callback1 = CallbackContext
    """Cselect_genderhoose to add mother or father."""
    level = update.callback_query.data
    context.user_data[CURRENT_LEVEL] = level

    text = 'Please select a option to continue'
    # perform swap operations here 

   

    buttons = [
        
        [
            # InlineKeyboardButton(text='Show data', callback_data=str(SHOWING)),
            InlineKeyboardButton(text='Back', callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text="perform swap", reply_markup=keyboard)

    return SELECTING_GENDER

def get_swap_history(update: Update, context: CallbackContext) -> None:
    update1 = update
    callback1 = CallbackContext
    """Cselect_genderhoose to add mother or father."""
    level = update.callback_query.data
    context.user_data[CURRENT_LEVEL] = level

    text = 'Please select a option to continue'
    # all the swap history operations here 
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    with app.app_context():
        user = db.session.query(Telegram).filter_by(telegramid=str(telegram_id)).first()
    if user == None or user.verified !="Yes": 
        res = "Your api data are not authentic, verify your Binance keys to continue using this bot."
    else:    
        with app.app_context():
            bsclient= dbOperations.getBinaceClient(str(telegram_id))
        res = binaceSwapOperations.getSwapHistory(bsclient)

    buttons = [
        
        [
            # InlineKeyboardButton(text='Show data', callback_data=str(SHOWING)),
            InlineKeyboardButton(text='Back', callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=res, reply_markup=keyboard)

    return SELECTING_GENDER



def end_second_level(update: Update, context: CallbackContext) -> None:
    """Return to top level conversation."""
    context.user_data[START_OVER] = True
    print('update1',update1)
    print('callback1', callback1)
    start(update, context)
    

    return END
 



# Third level callbacks
def select_feature(update: Update, context: CallbackContext) -> None:
    """Select a feature to update for the person."""
    update1 = update
    callback1 = CallbackContext

    buttons = [
        [
            InlineKeyboardButton(text='Api Key', callback_data=str(NAME)),
            InlineKeyboardButton(text='Api Secret', callback_data=str(AGE)),
            InlineKeyboardButton(text='Done', callback_data=str(END)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {GENDER: update.callback_query.data}
        text = 'Please select a feature to update.'

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = 'Got it! Please select a feature to update.'
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE

# def select_feature1(update: Update, context: CallbackContext) -> None:
#     """Select a feature to update for the person."""
#     update1 = update
#     callback1 = CallbackContext

#     buttons = [
#         [
#             InlineKeyboardButton(text='Continue', callback_data=str(NAME)),
#         ]
#     ]
#     keyboard = InlineKeyboardMarkup(buttons)

#     # If we collect features for a new person, clear the cache and save the gender
#     if not context.user_data.get(START_OVER):
#         context.user_data[FEATURES] = {GENDER: update.callback_query.data}
#         text = 'To perform swap trade\n 1. Copy and paste the swap trade message \n 2. Edit the message to your preferred the your quoteAsset,baseAsset and Quantity\n 3. click continue to perform swap trade'

#         update.callback_query.answer()
#         update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#     # But after we do that, we need to send a new message
#     else:
#         text = 'Got it! Please select a feature to update.'
#         update.message.reply_text(text=text, reply_markup=keyboard)

#     context.user_data[START_OVER] = False
#     return SELECTING_FEATURE1
# Third level callbacks
def select_feature1(update: Update, context: CallbackContext) -> None:
    """Select a feature to update for the person."""
    buttons = [
        [
            InlineKeyboardButton(text='Buy', callback_data=str(NAME)),
            InlineKeyboardButton(text='Sell', callback_data=str(AGE)),
        ], 
        [
            InlineKeyboardButton(text='Leverage', callback_data=str(LEVERAGE)),
            InlineKeyboardButton(text='Close', callback_data=str(CLOSE)),
        ],
        [
            InlineKeyboardButton(text='Position', callback_data=str(POSITION)),
            InlineKeyboardButton(text='Done', callback_data=str(END)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {GENDER: update.callback_query.data}
        text = 'Please select a operation to perform.'

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = 'Got it! Please select a operation to perform.'
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE1

def select_feature2(update: Update, context: CallbackContext) -> None:
    """Select a feature to update for the person."""
    update1 = update
    callback1 = CallbackContext


    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {GENDER: update.callback_query.data}
        text = 'select operation'

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text)
    # But after we do that, we need to send a new message
    else:
        text = 'Got it! Please select a feature to update.'
        update.message.reply_text(text=text)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE2


def select_feature3(update: Update, context: CallbackContext) -> None:
    """Select a feature to update for the person."""
    buttons = [
        [
            InlineKeyboardButton(text='Subscriptions', callback_data=str(SUBSCRIPTIONS)),
        ],
        [
            
            InlineKeyboardButton(text='Connect', callback_data=str(CONNECT)),
            InlineKeyboardButton(text='Disconnect', callback_data=str(DISCONNECT)),
        ], 
        [
            
            InlineKeyboardButton(text='set amount', callback_data=str(AGE)),
            InlineKeyboardButton(text='set Leverage', callback_data=str(LEVERAGE))
        ],
        [
            InlineKeyboardButton(text='check Positions', callback_data=str(POSITION)),
            InlineKeyboardButton(text='check Orders', callback_data=str(NAME)),
            
        ],
        [
            InlineKeyboardButton(text='Close', callback_data=str(CLOSE)),
        ],
        [
            InlineKeyboardButton(text='Done', callback_data=str(END)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {GENDER: update.callback_query.data}
        text = 'Please select a operation to perform.'

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = 'Got it! Please select a operation to perform.'
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE3

def ask_for_input(update: Update, context: CallbackContext) -> None:
    update1 = update
    callback1 = CallbackContext
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    text = 'Okay, tell me.'

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return TYPING
def ask_for_input1(update: Update, context: CallbackContext) -> None:
    update1 = update
    callback1 = CallbackContext
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    text = 'update feature'

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    
    return TYPING1

def select_feature_sub3(update: Update, context: CallbackContext):
    """Select a feature to update for the person."""
    update1 = update
    callback1 = CallbackContext

    buttons = [
        [
            # InlineKeyboardButton(text='Check subscription', callback_data=str(CSUBSCRIPTION)),
            InlineKeyboardButton(text='Plans', callback_data=str(NAME))
        ],
        [
            InlineKeyboardButton(text='Free Trial', callback_data=str(AGE))
        ],
        # [
        #     # InlineKeyboardButton(text='Link bot', callback_data=str(CSUBSCRIPTION)),
        #     # InlineKeyboardButton(text='Unlink bot', callback_data=str(NAME))
        # ]
        [
            InlineKeyboardButton(text='Back', callback_data=str(END)),
        ]


    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {GENDER: update.callback_query.data}
        text = 'Please select a feature to update.'

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = 'Got it! Please select a feature to update.'
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE4


def start_without_shipping_callback(update: Update, context: CallbackContext) -> None:
    """Sends an invoice without shipping-payment."""
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    chat_id = telegram_id
    title = "Trading Signal"
    description = "Payment for Binance automated trading signals"
    # select a payload just for you to recognize its the donation from your bot
    payload = "Custom-Payload"
    # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
    provider_token = "284685063:TEST:YjBiNjE5YTQ0YWZm"
    currency = "USD"
    # price in dollars
    price = 15
    # price * 100 so as to include 2 decimal points
    prices = [LabeledPrice("Starter", price * 100)]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True
    
    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )
    


# after (optional) shipping, it's the pre-checkout
def precheckout_callback(update: Update, context: CallbackContext) -> None:
    """Answers the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if query.invoice_payload != 'Custom-Payload':
        # answer False pre_checkout_query
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)


# finally, after contacting the payment provider...
def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    """Confirms the successful payment."""
    # do something after successfully receiving payment?
    update.message.reply_text("Thank you for your payment! test")
    context.user_data[START_OVER] = True
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    print("sjkshdosdhfd here", telegram_id)
    with app.app_context():
        status,subscription_type =checkSubscriptionStatus(telegram_id)
        if status==False:
            error,success =dbupdate(telegram_id, {"subscribed":True,"subscription_status":"ACTIVE", "subscription_start_date":datetime.now(),"subscription_type":"PRO","subscription_end_date":datetime.now() + timedelta(days=30)})
            if not success:
                print(error)
            else:
                adm_message = "Subscribed to premium plan"
                user, telegram_id, first_name, second_name = getUserDetails(update, context)
                sendAdminMessages(first_name, second_name,telegram_id,adm_message)
        elif status==True and subscription_type=="FREE TRIAL":
            error,success =dbupdate(telegram_id, {"subscribed":True, "subscription_status":"ACTIVE", "subscription_start_date":datetime.now(),"subscription_type":"PRO","subscription_end_date":datetime.now() + timedelta(days=30)})
            if not success:
                print(error)
            else:
                adm_message = "Subscribed to premium plan"
                user, telegram_id, first_name, second_name = getUserDetails(update, context)
                sendAdminMessages(first_name, second_name,telegram_id,adm_message)
        else:
            text="you are already in an active plan"
            # buttons = [
            # [
                
            #     InlineKeyboardButton(text='BACK', callback_data=str(END)),
            # ]
            # ]
            # keyboard = InlineKeyboardMarkup(buttons)
            # update.callback_query.answer()
            # update.callback_query.edit_message_text(text=text, reply_markup=keyboard)


    return select_feature3(update, context)


# after (optional) shipping, it's the pre-checkout
def precheckout_callback(update: Update, context: CallbackContext) -> None:
    """Answers the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if query.invoice_payload != 'Custom-Payload':
        # answer False pre_checkout_query
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)


def handleSubscription(update: Update, context: CallbackContext):
    """Select a feature to update for the person."""
    update1 = update
    callback1 = CallbackContext
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    text="Checking your subscriptions"
    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        
        context.user_data[FEATURES] = {GENDER: update.callback_query.data}
        context.user_data[CURRENT_FEATURE] = update.callback_query.data
        if context.user_data[CURRENT_FEATURE] == NAME:
            start_without_shipping_callback(update, context)

        if context.user_data[CURRENT_FEATURE] == CSUBSCRIPTION:
            text="Checking your subscriptions"

        if context.user_data[CURRENT_FEATURE] == AGE:
            with app.app_context():
                status,subscription_type =checkSubscriptionStatus(telegram_id)
                if status==False:
                    error,success =dbupdate(telegram_id, {"subscribed":True,"subscription_status":"ACTIVE", "subscription_start_date":datetime.now(),"subscription_type":"FREE TRIAL", "subscription_end_date":datetime.now() + timedelta(days=7)})    
                    text = "Your 7 days free trial activated"
                    adm_message = "Subscribed to 7 days Free Plan"
                    user, telegram_id, first_name, second_name = getUserDetails(update, context)
                    sendAdminMessages(first_name, second_name,telegram_id,adm_message)
                    if not success:
                        print(error)        
                if status==True:
                    text ="You are already in an active plan"
                
            

            
     

        buttons = [
        [
            
            InlineKeyboardButton(text='BACK', callback_data=str(ENDMANUAL)),
        ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = 'Got it! Please select a feature to update.'
        update.message.reply_text(text=text)

    context.user_data[START_OVER] = False
    return TYPING2


def ask_for_input3(update: Update, context: CallbackContext) -> None:
    update1 = update
    callback1 = CallbackContext
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    text="update feature"
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    # if context.user_data[CURRENT_FEATURE] == AGE:
    #     print("Selected amount")
    #     with app.app_context():
            
    #         pass
    # if context.user_data[CURRENT_FEATURE] == LEVERAGE:
    #     print("Selected leverage")
    # if context.user_data[CURRENT_FEATURE] == CLOSE:
    #     print("close orders")
    if context.user_data[CURRENT_FEATURE]==POSITION:
        with app.app_context():
            data = getAllOpenPositions(telegram_id)
        textp=str(data)
        buttons = [[InlineKeyboardButton(text='Back', callback_data=str(ENDMANUAL))]]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)
    elif context.user_data[CURRENT_FEATURE]==NAME:
        with app.app_context():
            data = getAllOpenOrders(telegram_id)
        textp=str(data)
        buttons = [[InlineKeyboardButton(text='Back', callback_data=str(ENDMANUAL))]]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)
    elif context.user_data[CURRENT_FEATURE]==CONNECT:
        print("Here on connect")
        with app.app_context():
            status, subscription_type =checkSubscriptionStatus(telegram_id)
            if status==False:
                textp = "Update declined, You have no active subscription"
                print(textp)
            else:
                error, resp=dbupdate(telegram_id, {"connected":True})
                if resp==True:
                    textp="Bot connected"
                    
                else:
                    print(error)
            buttons = [[InlineKeyboardButton(text='Back', callback_data=str(ENDMANUAL))]]
            keyboard = InlineKeyboardMarkup(buttons)
            update.callback_query.answer()
            update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)
    elif context.user_data[CURRENT_FEATURE]==DISCONNECT:
        print("Here on dosconnect")
        with app.app_context():
            status, subscription_type =checkSubscriptionStatus(telegram_id)
            if status==False:
                textp = "Update declined, You have no active subscription"
                print(textp)
            else:
                error, resp=dbupdate(telegram_id, {"connected":False})
                if resp==True:
                    textp="Bot connected"
                    # buttons = [[InlineKeyboardButton(text='Back', callback_data=str(ENDMANUAL))]]
                    # keyboard = InlineKeyboardMarkup(buttons)
                    # update.callback_query.answer()
                    # update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)
                else:
                    print(error)
            buttons = [[InlineKeyboardButton(text='Back', callback_data=str(ENDMANUAL))]]
            keyboard = InlineKeyboardMarkup(buttons)
            update.callback_query.answer()
            update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)
    elif context.user_data[CURRENT_FEATURE]==CLOSE:
        with app.app_context():
            data = getAllOpenOrderSymbol(telegram_id)
        
        textp=str(data)
        buttons = [[InlineKeyboardButton(text='Back', callback_data=str(ENDMANUAL))]]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)
    else:   
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text)
    
    return TYPING3

def ask_for_input2(update: Update, context: CallbackContext) -> None:
    update1 = update
    callback1 = CallbackContext
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    text = '{"quoteAsset":"BUSD", "baseAsset":"EUR", "quoteQty":10}'

    if context.user_data[CURRENT_FEATURE] == str(WEBHOOK):
        user, telegram_id, first_name, second_name = getUserDetails(update, context)

        # check if authentication token exists
        with app.app_context():
            authenticated = bool(db.session.query(Telegram).filter_by(telegramid = telegram_id).first())
            user = db.session.query(Telegram).filter_by(telegramid=telegram_id).first()
            # if token in toList:
            if authenticated == True and user.verified=="Yes": 
                bot_user = db.session.query(Telegram).filter_by(telegramid=str(telegram_id)).first()
                if bot_user.auth_token ==None:
                    auth_token = security.generate_auth_token()
                    db.session.query(Telegram).filter_by(telegramid=str(telegram_id)).update({"auth_token":auth_token})
                    db.session.commit()
                else:
                    auth_token = bot_user.auth_token    
                    

                text3 = 'You need set an automated process. Open your http://www.tradingview.com/ account, create an alert \n \n'
                text4 = 'Add http://83.136.219.69/webhook/{0} on the webhook section and paste a message similar to this one below on the message section \n \n'.format(auth_token)     
                text5 = ''+'{"quoteAsset":"BUSD", "baseAsset":"EUR", "quoteQty":10}'+'\n \n'
                

            
                textp =  text3 + text4 + text5

            else:
                textp= 'you are not authenticated to use this bot\nCreate an account from the bot and try again\n'
    buttons = [
        [
            
            InlineKeyboardButton(text='BACK', callback_data=str(ENDMANUAL)),
        ]
    ]


    if context.user_data[CURRENT_FEATURE] == str(WEBHOOKR):
        auth_token = security.generate_auth_token()
        user, telegram_id, first_name, second_name = getUserDetails(update, context)
        # check if authentication token exists
        with app.app_context():
            authenticated = bool(db.session.query(Telegram).filter_by(telegramid = telegram_id).first())
            user = db.session.query(Telegram).filter_by(telegramid=telegram_id).first()
            # if token in toList:
            if authenticated == True and user.verified=="Yes": 
                bot_user = db.session.query(Telegram).filter_by(telegramid=str(telegram_id)).first()
                db.session.query(Telegram).filter_by(telegramid=str(telegram_id)).update({"auth_token":auth_token})
                db.session.commit()
                    

                text3 = 'Your webhook token updated successifully. Open your http://www.tradingview.com/ account, create an alert \n \n'
                text4 = 'Add http://83.136.219.69/webhook/{0} on the webhook section and paste a message similar to this one below on the message section \n \n'.format(auth_token)     
                text5 = ''+'{"quoteAsset":"BUSD", "baseAsset":"EUR", "quoteQty":10}'+'\n \n'
            

        
                textp =  text3 + text4 + text5
            else:
                textp= 'you are not authenticated to use this bot\nCreate an account from the bot and try again\n'

    buttons = [
        [
            
            InlineKeyboardButton(text='BACK', callback_data=str(ENDMANUAL)),
        ]
    ] 
   
    
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)


    
    return ENDMANUAL

def save_input(update: Update, context: CallbackContext) -> None:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    user_data[FEATURES][user_data[CURRENT_FEATURE]] = update.message.text

    user_data[START_OVER] = True

    return select_feature(update, context)
def swapTradeProcessor(update: Update, context: CallbackContext):
    user_data = context.user_data
    swap_payload = user_data[FEATURES][user_data[CURRENT_FEATURE]]
    print("printing text",swap_payload)
    user, telegram_id, first_name, second_name = getUserDetails(update, context)
    with app.app_context():
        user = db.session.query(Telegram).filter_by(telegramid=str(telegram_id)).first()
    if user == None or user.verified !="Yes": 
        textp = "Your api data are not authentic, verify your Binance keys to continue using this bot."
    else:    
        if swap_payload == "":
            textp = "Invalid message"

        else:
            try:
                json.loads(swap_payload)
                with app.app_context():
                    bclient = dbOperations.getBinaceClient(str(telegram_id))
                textp = binaceSwapOperations.performSwap(bclient, json.loads(swap_payload))
            except:
                textp = "Invalid Swap message format"
    buttons = [[InlineKeyboardButton(text='Back', callback_data=str(END))]]
    keyboard = InlineKeyboardMarkup(buttons)
    # if context.user_data.get(START_OVER):

    #     update.callback_query.edit_message_text(text=textp, reply_markup=keyboard)
    #     # update1.message.reply_text(text=text, reply_markup=keyboard)
    # else:
       
    #     update.message.reply_text(
    #         'Hello, Welcome to Binance Swap bot'
    #     )
    update.message.reply_text(text=textp, reply_markup=keyboard)

    context.user_data[START_OVER] = False


    return SHOWING
           
        

def save_input1(update: Update, context: CallbackContext) -> None:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    user_data[FEATURES][user_data[CURRENT_FEATURE]] = update.message.text

    user_data[START_OVER] = True
   
    return select_feature1(update, context)


def save_input3(update: Update, context: CallbackContext) -> None:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    user_data[FEATURES][user_data[CURRENT_FEATURE]] = update.message.text
    # if context.user_data[CURRENT_FEATURE] == AGE:
    #     amount= user_data[FEATURES][user_data[CURRENT_FEATURE]]
    #     with app.app_context():
    #         status, subscription_type =checkSubscriptionStatus(telegram_id)
    #         if status==False:
    #             text = "You have no active subscription"
    #             print(text)
    #         else:
            
    #             dbupdate(telegram_id,{'amount':amount})
    #             print("Updated amount")

    user_data[START_OVER] = True
    
   
    return select_feature3(update, context)


def end_describing_manual(update: Update, context: CallbackContext) -> None:
    """End gathering of features and return to parent conversation."""
    user_data = context.user_data
    level = user_data[CURRENT_LEVEL]
    if not user_data.get(level):
        user_data[level] = []
    user_data[level].append(user_data[FEATURES])

    # Print upper level menu
    if level == SELF:
        user_data[START_OVER] = True

        start(update, context)
    else:
        select_level(update, context)

    return END

def end_describing(update: Update, context: CallbackContext) -> None:
    """End gathering of features and return to parent conversation."""
    user_data = context.user_data
    level = user_data[CURRENT_LEVEL]
    if not user_data.get(level):
        user_data[level] = []
    user_data[level].append(user_data[FEATURES])
    if level == 'SELF':
        pass
       
    else:
        # select_level(update, context)
        show_data(update, context)
        
    return END


def stop_nested(update: Update, context: CallbackContext) -> None:
    """Completely end conversation from within nested conversation."""
    user_data = context.user_data
    update.message.reply_text('Okay, bye.')
    update.message.reply_text('Type, /start to restart bot.')
    user_data[START_OVER] = False
    return STOPPING


def production_warning(env, args):
    if len(args):
        env = 'PRODUCTION' if env == 'prod' else 'STAGING'
        cmd = ' '.join(args)
        # allow some time to cancel commands
        for i in [4, 3, 2, 1]:
            click.echo(f'!! {env} !!: Running "{cmd}" in {i} seconds')
            time.sleep(1)



def main():

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    bot_token =Config.BOT_TOKEN
    updater = Updater(bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Set up third level ConversationHandler (collecting features)
    
    # Set up third level ConversationHandler (collecting features)
    description_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                select_feature, pattern='^' + str(MALE) + '$' #API data
            
            ),
            CallbackQueryHandler(
                select_feature1, pattern='^' + str(FEMALE) + '$' #API data
            
            ),
            CallbackQueryHandler(
            select_feature2, pattern='^' + str(AUTOMATED) + '$' #Automated trading
        
        ),
        CallbackQueryHandler(
            select_feature3, pattern='^' + str(COPYTRADE) + '$' #COPY TRADING
        
        ),
        
        ],
        states={
            SELECTING_FEATURE: [
                # this ask for input is used by verify keys level   SELF.
                CallbackQueryHandler(ask_for_input, pattern='^(?!' + str(END) + ').*$')
            ],
            TYPING: [MessageHandler(Filters.text & ~Filters.command, save_input)],
            
            SELECTING_FEATURE1: [
                CallbackQueryHandler(ask_for_input1, pattern='^(?!' + str(END) + ').*$'),
            ],
            TYPING1: [MessageHandler(Filters.text & ~Filters.command, save_input1)],

            SELECTING_FEATURE2: [
                CallbackQueryHandler(ask_for_input2, pattern='^(?!' + str(ENDMANUAL) + ').*$'),
            ],
            SELECTING_FEATURE3: [

                CallbackQueryHandler(select_feature_sub3, pattern='^' + str(SUBSCRIPTIONS) + '*$' ),#SUBSCRIPTIONS
                CallbackQueryHandler(ask_for_input3, pattern='^(?!' + str(END) + ').*$'),
                
            ],
           
            SELECTING_FEATURE4: [
                CallbackQueryHandler(handleSubscription, pattern='^(?!' + str(END) + ').*$'),
            ],
            

            TYPING2: [MessageHandler(Filters.successful_payment, successful_payment_callback)],
            TYPING3: [MessageHandler(Filters.text & ~Filters.command, save_input3)],

            
 
        },
        fallbacks=[
            CallbackQueryHandler(end_describing_manual, pattern='^' + str(ENDMANUAL) + '$'),
            CallbackQueryHandler(end_describing, pattern='^' + str(END) + '$'),
            CommandHandler('stop', stop_nested),
        ],
        map_to_parent={
            
            # Return to second level menu
            END: SELECTING_LEVEL,
           
            # End conversation alltogether
            STOPPING: STOPPING,
        },
    )

    # Set up second level ConversationHandler (adding a person)
    # add_member_conv = ConversationHandler(
    #     entry_points=[CallbackQueryHandler(select_level, pattern='^' + str(ADDING_MEMBER) + '$')],
    #     states={
    #         # SELECTING_LEVEL: [
    #         #     CallbackQueryHandler(select_feature, pattern=f'^{MALE}$|')
    #         # ],
    #         SELECTING_LEVEL: [
    #             # CallbackQueryHandler(select_gender, pattern=f'^{PARENTS}$|^{CHILDREN}$|^{NEIGHBORS}$|^{FOREIGNERS}$'),
    #             CallbackQueryHandler(get_all_swaps, pattern=f'^{PARENTS}$'),
    #             CallbackQueryHandler(request_swap, pattern=f'^{CHILDREN}$'),
    #             CallbackQueryHandler(perform_swap, pattern=f'^{NEIGHBORS}$'),
    #             CallbackQueryHandler(get_swap_history, pattern=f'^{FOREIGNERS}$')
    #         ],
    #         SELECTING_GENDER: [description_conv],
    #     },
    #     fallbacks=[
    #         CallbackQueryHandler(show_data, pattern='^' + str(SHOWING) + '$'),
    #         CallbackQueryHandler(end_second_level, pattern='^' + str(END) + '$'),
    #         CommandHandler('stop', stop_nested),
    #     ],
    #     map_to_parent={
    #         # After showing data return to top level menu
    #         SHOWING: SHOWING,
    #         # Return to top level menu
    #         END: SELECTING_ACTION,
    #         # End conversation alltogether
    #         STOPPING: END,
    #     },
    # )

    add_member_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_level, pattern='^' + str(ADDING_MEMBER) + '$')],
        states={
            SELECTING_LEVEL: [
                CallbackQueryHandler(select_gender, pattern=f'^{PARENTS}$|^{CHILDREN}$')
            ],
            SELECTING_GENDER: [description_conv],
        },
        fallbacks=[
            CallbackQueryHandler(show_data, pattern='^' + str(SHOWING) + '$'),
            CallbackQueryHandler(end_second_level, pattern='^' + str(END) + '$'),
            CommandHandler('stop', stop_nested),
        ],
        map_to_parent={
            # After showing data return to top level menu
            SHOWING: SHOWING,
            # Return to top level menu
            END: SELECTING_ACTION,
            # End conversation alltogether
            STOPPING: END,
        },
    )# Set up second level ConversationHandler (adding a person)
    add_member_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_level, pattern='^' + str(ADDING_MEMBER) + '$')],
        states={
            SELECTING_LEVEL: [
                CallbackQueryHandler(select_gender, pattern=f'^{PARENTS}$|^{CHILDREN}$')
            ],
            SELECTING_GENDER: [description_conv],
        },
        fallbacks=[
            CallbackQueryHandler(show_data, pattern='^' + str(SHOWING) + '$'),
            CallbackQueryHandler(end_second_level, pattern='^' + str(END) + '$'),
            CommandHandler('stop', stop_nested),
        ],
        map_to_parent={
            # After showing data return to top level menu
            SHOWING: SHOWING,
            # Return to top level menu
            END: SELECTING_ACTION,
            # End conversation alltogether
            STOPPING: END,
        },
    )
    add_self_conv = ConversationHandler(
        entry_points=[ CallbackQueryHandler(adding_self, pattern='^' + str(ADDING_SELF) + '$')],
        states={
            DESCRIBING_SELF: [description_conv],
           
        },
        fallbacks=[
            CallbackQueryHandler(show_data, pattern='^' + str(SHOWING) + '$'),
            CallbackQueryHandler(end_second_level, pattern='^' + str(END) + '$'),
            CommandHandler('stop', stop_nested),
        ],
        map_to_parent={
            # After showing data return to top level menu
            SHOWING: SHOWING,
            # Return to top level menu
            END: SELECTING_ACTION,
            # End conversation alltogether
            STOPPING: END,
        },
    )

    # Set up top level ConversationHandler (selecting action)
    # Because the states of the third level conversation map to the ones of the econd level
    # conversation, we need to make sure the top level conversation can also handle them
    selection_handlers = [
        add_member_conv,
        add_self_conv,
        # CallbackQueryHandler(show_data, pattern='^' + str(SHOWING) + '$'),
        # CallbackQueryHandler(adding_self, pattern='^' + str(ADDING_SELF) + '$'),
        CallbackQueryHandler(end, pattern='^' + str(END) + '$'),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SHOWING: [CallbackQueryHandler(start, pattern='^' + str(END) + '$')],
            SELECTING_ACTION: selection_handlers,
            SELECTING_LEVEL: selection_handlers,
            # DESCRIBING_SELF: [description_conv],
            STOPPING: [CommandHandler('start', start)],
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    dispatcher.add_handler(conv_handler)
   # Pre-checkout handler to final check
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    # Success! Notify your user!
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    # Then, we need to run the loop with a task
    #loop.run_until_complete(main())

    #loop.create_task(main())
    p4 = Process(target = main)
    p4.start()
    # with app.app_context():
    # app.run(debug = False, host="0.0.0.0",port=85)
    # app.run(debug = False, host="0.0.0.0",port=5000)
    # app.run(host="0.0.0.0",port=80)

    #app.run(host="212.49.95.112:5055")
    #main()