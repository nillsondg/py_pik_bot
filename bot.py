import datetime
import hashlib

import pymongo
import telebot
from telebot import types

from states import *
import sql
from config import TOKEN

bot = telebot.AsyncTeleBot(TOKEN)

client = pymongo.MongoClient()
db = client.users

SOLD_CMD = "sold"
FORECAST_CMD = "forecast"
STATE_SELECTOR = "selector"
NEED_AUTH = "need_auth"
user_state = dict()
sql_server = sql.SQL()


def get_current_state(uid):
    if uid not in user_state:
        user_state[uid] = State.none
    if not check_user_id_in_db(uid):
        return NEED_AUTH
    return user_state[uid]


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Это может помочь… или нет")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardHide(selective=False)
    bot.reply_to(message, "Привет!", reply_markup=markup)
    if not check_user_id_in_db(message.from_user.uid):
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


@bot.message_handler(commands=[SOLD_CMD, FORECAST_CMD])
def start_handler(msg):
    current_state = get_current_state(msg.chat.id)
    if current_state == State.none:
        user_state[msg.chat.id] = State.pik_today
    elif current_state == NEED_AUTH:
        check_auth(msg)
        return
    state_handler(msg)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) != State.none)
def state_handler(msg):
    if get_current_state(msg.chat.id) == STATE_SELECTOR:
        user_state[msg.chat.id] = State.get_state_by_description(msg.text)
    # todo handle
    bot.reply_to(msg, "proc 1", reply_markup=types.ReplyKeyboardHide())
    print_step_keyboard(msg, user_state[msg.chat.id])


def print_step_keyboard(msg, state):
    markup = types.ReplyKeyboardMarkup()
    next_states = StateTransitions.get_transition_for_state(state)
    if len(next_states) == 0:
        user_state[msg.chat.id] = State.none
        return
    for next_state in next_states:
        markup.add(types.KeyboardButton(next_state.description))
    bot.send_message(msg.chat.id, "Choose state:", reply_markup=markup)
    user_state[msg.chat.id] = STATE_SELECTOR


# only used for console output now
def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)


bot.set_update_listener(listener)
bot.polling()
