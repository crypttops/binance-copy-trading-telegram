# pip install python-dotenv python-telegram-bot
# create a .env file with
# BOT_TOKEN=...
# in the same dir as of this script

import logging
from dotenv import load_dotenv
from telegram.ext.filters import Filters
from telegram import ParseMode
import os
from telegram.ext.messagehandler import MessageHandler
from telegram import Update, replymarkup
from telegram.ext import (Updater,
                          PicklePersistence,
                          CommandHandler,
                          CallbackQueryHandler,
                          CallbackContext,
                          ConversationHandler)
from telegram import InlineKeyboardButton as IKB, InlineKeyboardMarkup, ForceReply


load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')


def start(update: Update, context: CallbackContext):
    ''' Replies to start command '''
    update.message.reply_text('Hi! I am alive. Click /post to create a post')


def main_menu(update: Update, context: CallbackContext):
    ''' Entry point of conversation  this gives  buttons to user'''

    update.message.reply_text('''Choose your option:\n
    /add : to add a button
    /preview : to preview current post
    /send : to send current post
    /cancel : to delete current post
    ''',)


def add_button(update: Update, context: CallbackContext):
    args = ' '.join(context.args).strip()
    if not args:
        update.message.reply_text(
            'Please send the text and link with the command. \nExample: \n\n`/add Click here - https://aahnik.github.io`',parse_mode= ParseMode.MARKDOWN)
        return
    try:
        splitted = args.split('-')
        print(splitted)
        text = splitted[0].strip()
        url = splitted[1].strip()
        print(text,url)
    except Exception as err:
        update.message.reply_text(str(err)[:2000])
        return

    user_d = context.user_data
    if not 'buttons' in user_d:
        user_d['buttons'] = []
    user_d['buttons'].append([IKB(text, url=url)])
    update.message.reply_text('Done')
    main_menu(update,context)


def preview(update: Update, context: CallbackContext):
    user_d = context.user_data
    buttons = user_d.get('buttons')
    if buttons:
        update.message.reply_text(
            'Buttons Preview', reply_markup=InlineKeyboardMarkup(buttons))
    else:
        update.message.reply_text('No buttons added yet')
    main_menu(update,context)

def send(update: Update, context: CallbackContext):
    update.message.reply_text('Sent message')
    #  send the message

    user_d = context.user_data
    user_d.clear()


def cancel(update: Update, context: CallbackContext):
    user_d = context.user_data
    user_d.clear()
    update.message.reply_text('Cleared user data')
    main_menu(update,context)


if __name__ == "__main__":

    updater = Updater(token=BOT_TOKEN)

    dispatcher = updater.dispatcher

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    _handlers = {}

    _handlers['start_handler'] = CommandHandler('start', start)

    _handlers['post_hanlder'] = CommandHandler('post', main_menu)

    _handlers['add_button_handler'] = CommandHandler('add', add_button)
    _handlers['preview_handler'] = CommandHandler('preview', preview)
    _handlers['cancel_handler'] = CommandHandler('cancel', cancel)
    _handlers['send_handler'] = CommandHandler('send', send)

    for name, _handler in _handlers.items():
        print(f'Adding handler {name}')
        dispatcher.add_handler(_handler)

    updater.start_polling()

    updater.idle()