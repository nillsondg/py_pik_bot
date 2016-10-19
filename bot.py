import hashlib
import json
from collections import OrderedDict

import telebot
from telebot import types

from api_token import TOKEN

bot = telebot.TeleBot(TOKEN)
users = []
auth_needed = False

with open('state_map.json') as f:
    states = json.load(f, object_pairs_hook=OrderedDict)

STATE_1 = "state1"
STATE_2 = "state2"
STATE_3 = "state3"
STATE_SELECTOR = "selector"
user_state = dict()


def get_current_state(uid):
    if uid not in user_state:
        user_state[uid] = 0
    return user_state[uid]


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Это может помочь… или нет")


@bot.message_handler(commands=['start'])
# @bot.message_handler(func=lambda m: not auth_needed)
def send_welcome(message):
    markup = types.ReplyKeyboardHide(selective=False)
    bot.reply_to(message, "Привет!", reply_markup=markup)
    username = message.from_user.username
    if username not in users:
        auth_request()
        bot.send_message(message.chat.id, "Введите кодовое слово")
        bot.register_next_step_handler(message, check_auth)


def check_auth(message):
    if check_code(message.text):
        users.append(message.from_user.username)
        bot.reply_to(message, "Добро пожаловать")
        auth_granted()
    else:
        bot.reply_to(message, "Неверно, попроуйте еще")
        bot.register_next_step_handler(message, check_auth)


def check_code(code):
    return hashlib.md5(code.encode('utf-8')).hexdigest() == "bc250e0d83c37b0953ada14e7bbc1dfd"


def auth_request():
    global auth_needed
    auth_needed = True


def auth_granted():
    global auth_needed
    auth_needed = False


user_dict = {}


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
    print_step_keyboard(msg, STATE_1)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_2)
@bot.message_handler(commands=[STATE_2])
def proc2(msg):
    bot.reply_to(msg, "proc 2", reply_markup=types.ReplyKeyboardHide())
    print_step_keyboard(msg, STATE_2)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_3)
@bot.message_handler(commands=[STATE_3])
def proc3(msg):
    bot.reply_to(msg, "proc 3", reply_markup=types.ReplyKeyboardHide())
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
