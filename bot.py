import datetime
import cherrypy
import hashlib

import pymongo
import telebot
import os
from telebot import types
import logging

from states import *
from data import DataProvider
from config import TOKEN

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

client = pymongo.MongoClient()
db = client.users

SOLD_CMD = "sold"
FORECAST_CMD = "forecast"
SMS_CMD = "sms"
NEED_AUTH = "need_auth"
user_state = dict()


def get_current_state(uid):
    if uid not in user_state:
        user_state[uid] = State.none
    if not check_user_id_in_db(uid):
        # todo refactor
        return NEED_AUTH
    return user_state[uid]


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
    markup = types.ReplyKeyboardHide(selective=False)
    bot.reply_to(message, "Привет!", reply_markup=markup)
    if not check_user_id_in_db(message.from_user.id):
        bot.send_message(message.chat.id, "Введите кодовое слово")
        bot.register_next_step_handler(message, check_auth)
    else:
        update_user_auth(message.from_user)


def check_auth(message):
    if check_code(message.text):
        bot.reply_to(message, "Добро пожаловать")
        add_user_into_db(message.from_user)
    else:
        bot.reply_to(message, "Неверно, попробуйте еще")
        bot.register_next_step_handler(message, check_auth)


def check_code(code):
    return hashlib.md5(code.encode('utf-8')).hexdigest() == "bc250e0d83c37b0953ada14e7bbc1dfd"


def check_user_id_in_db(uid):
    return db.users.find_one(str(uid)) is not None


def add_user_into_db(user):
    db.users.insert({
        "_id": str(user.id),
        "last_name": user.last_name,
        "first_name": user.first_name,
        "username": user.username,
        "added_date": datetime.datetime.utcnow(),
        "last_auth": datetime.datetime.utcnow()
    })


def update_user_auth(user):
    db.users.update({'_id': str(user.id)}, {"$set": {'last_auth': datetime.datetime.utcnow()}})


@bot.message_handler(commands=['cancel'])
def cancel(msg):
    user_state[msg.chat.id] = State.none
    bot.reply_to(msg, "Отменено", reply_markup=types.ReplyKeyboardHide())


@bot.message_handler(commands=[SOLD_CMD])
def sold(msg):
    start_handler(msg, Type.sold)


@bot.message_handler(commands=[FORECAST_CMD])
def forecast(msg):
    start_handler(msg, Type.forecast)


@bot.message_handler(commands=[SMS_CMD])
def sms(msg):
    start_handler(msg, Type.sms)


def start_handler(msg, state_type):
    current_state = get_current_state(msg.chat.id)
    if current_state == NEED_AUTH:
        check_auth(msg)
        return
    # init state
    elif current_state == State.none:
        current_state = State.pik_today
        current_state.type = state_type
    # change branch
    elif isinstance(current_state, State) and current_state.type != state_type:
        current_state.type = state_type
    # reset state
    elif isinstance(current_state, State) and current_state.type == state_type:
        current_state = State.pik_today
        current_state.type = state_type

    bot.send_chat_action(msg.chat.id, 'typing')
    result = "Error occurred"
    try:
        result = DataProvider.request(current_state)
    except Exception as e:
        print("Error!")
        print(e)
        current_state = State.none
    bot.reply_to(msg, result, reply_markup=types.ReplyKeyboardHide())
    print_step_keyboard(msg, current_state)
    user_state[msg.chat.id] = current_state


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) != State.none)
def state_handler(msg):
    current_state = get_current_state(msg.chat.id)
    selected_state = State.get_state_by_description(msg.text)
    if selected_state == State.none:
        return
    else:
        user_state[msg.chat.id] = State.none
    selected_state.type = current_state.type
    bot.send_chat_action(msg.chat.id, 'typing')
    result = "Error occurred"
    try:
        result = DataProvider.request(selected_state)
    except Exception as e:
        print("Error!")
        print(e)
        selected_state = State.none
    bot.reply_to(msg, result, reply_markup=types.ReplyKeyboardHide())
    print_step_keyboard(msg, selected_state)
    user_state[msg.chat.id] = selected_state


def print_step_keyboard(msg, state):
    markup = types.ReplyKeyboardMarkup()
    next_states = StateTransitions.get_transition_for_state(state)
    if len(next_states) == 0:
        user_state[msg.chat.id] = State.none
        return
    for next_state in next_states:
        markup.add(types.KeyboardButton(next_state.description))
    bot.send_message(msg.chat.id, "Выберете следующий запрос", reply_markup=markup)
    # bot.register_next_step_handler(msg, state_handler)


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
