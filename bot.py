import datetime
import hashlib
import json
from collections import OrderedDict

import pymongo
import telebot
from telebot import types

from filter import *

from api_token import TOKEN

bot = telebot.TeleBot(TOKEN)

client = pymongo.MongoClient()
db = client.users


with open('state_map.json') as f:
    states = json.load(f, object_pairs_hook=OrderedDict)

STATE_1 = "state1"
STATE_2 = "state2"
STATE_3 = "state3"
STATE_SELECTOR = "selector"
user_state = dict()
user_filter = dict()


def get_current_state(uid):
    if uid not in user_state:
        user_state[uid] = 0
    return user_state[uid]


def get_current_filter(uid):
    if uid not in user_filter:
        user_filter[uid] = Filter()
    return user_filter[uid]


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Это может помочь… или нет")


@bot.message_handler(commands=['start'])
# @bot.message_handler(func=lambda m: not auth_needed)
def send_welcome(message):
    markup = types.ReplyKeyboardHide(selective=False)
    bot.reply_to(message, "Привет!", reply_markup=markup)
    if not check_user_in_db(message.from_user):
        bot.send_message(message.chat.id, "Введите кодовое слово")
        bot.register_next_step_handler(message, check_auth)
    else:
        update_user_auth(message.from_user)


def check_auth(message):
    if check_code(message.text):
        bot.reply_to(message, "Добро пожаловать")
        add_user_into_db(message.from_user)
    else:
        bot.reply_to(message, "Неверно, попроуйте еще")
        bot.register_next_step_handler(message, check_auth)


def check_code(code):
    return hashlib.md5(code.encode('utf-8')).hexdigest() == "bc250e0d83c37b0953ada14e7bbc1dfd"


def check_user_in_db(user):
    return db.users.find_one(str(user.id)) is not None


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
    user_state[msg.chat.id] = 0
    bot.reply_to(msg, "Отменено", reply_markup=types.ReplyKeyboardHide())


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_SELECTOR)
def selector(msg):
    if msg.text in states:
        if msg.text == STATE_2:
            proc2(msg)
        if msg.text == STATE_3:
            proc3(msg)
    user_state[msg.chat.id] = 0


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_1)
@bot.message_handler(commands=[STATE_1])
def proc1(msg):
    bot.reply_to(msg, "proc 1", reply_markup=types.ReplyKeyboardHide())
    cur_filter = get_current_filter(msg.chat.id)
    cur_filter.set_time(Time.today)
    cur_filter.set_source(Source.pik)
    print_step_keyboard(msg, STATE_1)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_2)
@bot.message_handler(commands=[STATE_2])
def proc2(msg):
    bot.reply_to(msg, "proc 2", reply_markup=types.ReplyKeyboardHide())
    cur_filter = get_current_filter(msg.chat.id)
    cur_filter.set_time(Time.today)
    cur_filter.set_source(Source.morton)
    print_step_keyboard(msg, STATE_2)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_3)
@bot.message_handler(commands=[STATE_3])
def proc3(msg):
    bot.reply_to(msg, "proc 3", reply_markup=types.ReplyKeyboardHide())
    cur_filter = get_current_filter(msg.chat.id)
    if cur_filter.is_clear():
        cur_filter.set_time(Time.today)
        cur_filter.set_source(Source.pik)
    bot.send_message(msg.chat.id, str(cur_filter.time) + " " + str(cur_filter.source))
    print_step_keyboard(msg, STATE_3)


def print_step_keyboard(msg, state):
    markup = types.ReplyKeyboardMarkup()
    buttons = states[state]["next"]
    if len(buttons) == 0:
        user_state[msg.chat.id] = 0
        return
    for button in buttons:
        markup.add(types.KeyboardButton(button))
    bot.send_message(msg.chat.id, "Choose state:", reply_markup=markup)
    user_state[msg.chat.id] = STATE_SELECTOR


bot.polling()
