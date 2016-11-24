import cherrypy
import hashlib

import telebot
import os
from telebot import types
import logging
import mongodb

from states import *
from data import DataProvider
from config import TOKEN
import datetime

os.environ['NO_PROXY'] = 'https://api.telegram.org'


WEBHOOK_HOST = 'tgbot.pik.ru'
WEBHOOK_PORT = 443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (TOKEN)

print(WEBHOOK_URL_BASE)
print(WEBHOOK_URL_PATH)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(TOKEN)

SOLD_CMD = "sold"
FORECAST_CMD = "forecast"
SMS_CMD = "sms"
NEED_AUTH = "need_auth"
user_state = dict()
user_last_state = dict()
user_last_request_time = dict()
mongo = mongodb.MongoDB()


def get_current_state(uid):
    if uid not in user_state:
        user_state[uid] = State.none
    return user_state[uid]


def get_user_last_state(uid):
    if uid not in user_last_state:
        user_last_state[uid] = State.none
    return user_last_state[uid]


def get_last_request_time(uid):
    if uid not in user_last_request_time:
        user_last_request_time[uid] = None
    return user_last_request_time[uid]


def set_last_request_time_now(uid):
    user_last_request_time[uid] = datetime.datetime.now()


# WebhookServer, process webhook calls
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
           'content-type' in cherrypy.request.headers and \
           cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Это может помочь… или нет")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not mongo.check_user_id_in_db(message.from_user.id):
        bot.send_message(message.chat.id, "Введите кодовое слово")
        bot.register_next_step_handler(message, check_auth)
    else:
        mongo.update_user_auth(message.from_user)
        print_sms_keyboard(message, "Введите команду")


def check_auth(message):
    if check_code(message.text):
        print_sms_keyboard(message, "Добро пожаловать")
        mongo.add_user_into_db(message.from_user)
    else:
        bot.reply_to(message, "Неверно, попробуйте еще", disable_notification=True)
        bot.register_next_step_handler(message, check_auth)


def check_code(code):
    return hashlib.md5(code.encode('utf-8')).hexdigest() == "70dda5dfb8053dc6d1c492574bce9bfd"


@bot.message_handler(commands=[SMS_CMD])
def sms(msg):
    start_handler(msg, State.pik_today)


@bot.message_handler(func=lambda msg: msg.text == Source.pik.value)
def sms_pik(msg):
    start_handler(msg, State.pik_today)


@bot.message_handler(func=lambda msg: msg.text == Source.morton.value)
def sms_morton(msg):
    start_handler(msg, State.morton_today)


def start_handler(msg, state):
    state.type = Type.sms

    current_state = get_current_state(msg.chat.id)
    if not mongo.check_user_id_in_db(msg.from_user.id):
        check_auth(msg)
        return

    # switch to prevent next request before first done
    if current_state != State.none:
        return
    else:
        user_state[msg.chat.id] = state
    process_request(msg, state)
    user_state[msg.chat.id] = State.none
    set_last_request_time_now(msg.chat.id)
    user_last_state[msg.chat.id] = state


def process_request(msg, state):
    bot.send_chat_action(msg.chat.id, 'typing')
    result = "Произошла ошибка"
    try:
        if get_user_last_state(msg.chat.id) == state:
            result = DataProvider.request_with_cache(state, get_last_request_time(msg.chat.id))
        else:
            result = DataProvider.request_with_cache(state, None)
    except Exception as e:
        # todo log
        print("Error!")
        print(e)
        state = State.none

    if isinstance(result, (list, tuple)):
        bot.send_message(msg.chat.id, format_cache_time(result[1]), disable_notification=True, parse_mode="Markdown")
        bot.send_message(msg.chat.id, result[0], disable_notification=True)
    else:
        bot.send_message(msg.chat.id, result, disable_notification=True)

    return state


def format_cache_time(date_time):
    return "_@" + date_time.strftime("%H:%M:%S") + "_"


def print_sms_keyboard(msg, text):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    markup.row(types.KeyboardButton(Source.pik.value), types.KeyboardButton(Source.morton.value))
    bot.send_message(msg.chat.id, text, reply_markup=markup, disable_notification=True)


# only used for console output now
def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)


bot.set_update_listener(listener)
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT
})
cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
