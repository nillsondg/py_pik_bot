import datetime
import hashlib
import json
from collections import OrderedDict

import pymongo
import telebot
from telebot import types

import sql
from config import TOKEN
from filter import *

bot = telebot.TeleBot(TOKEN)

client = pymongo.MongoClient()
db = client.users

with open('state_map.json') as f:
    states = json.load(f, object_pairs_hook=OrderedDict)

# todo DRY -> state class needed
CMD_SOLD = "sold"
CMD_FORECAST = "forecast"
STATE_SOLD_ALL_TODAY = "sold_all_today"
STATE_SOLD_ALL_YESTERDAY = "sold_all_yesterday"
STATE_SOLD_REG_TODAY = "sold_reg_today"
STATE_SOLD_REG_YESTERDAY = "sold_reg_yesterday"
STATE_SOLD_MOS_TODAY = "sold_mos_today"
STATE_SOLD_MOS_YESTERDAY = "sold_mos_yesterday"

STATE_SELECTOR = "selector"
user_state = dict()
user_filter = dict()
sql_server = sql.SQL()


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
        bot.reply_to(message, "Неверно, попробуйте еще")
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
        if msg.text == STATE_SOLD_ALL_TODAY:
            sold_all_today(msg)
        if msg.text == STATE_SOLD_ALL_YESTERDAY:
            sold_all_yesterday(msg)
        if msg.text == STATE_SOLD_REG_TODAY:
            sold_reg_today(msg)
        if msg.text == STATE_SOLD_REG_YESTERDAY:
            sold_reg_yesterday(msg)
        if msg.text == STATE_SOLD_MOS_TODAY:
            sold_mos_today(msg)
        if msg.text == STATE_SOLD_MOS_YESTERDAY:
            sold_mos_yesterday(msg)
    user_state[msg.chat.id] = 0


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_SOLD_ALL_TODAY)
@bot.message_handler(commands=[CMD_SOLD])
def sold_all_today(msg):
    cur_filter = get_current_filter(msg.chat.id)
    cur_filter.set_time(Time.today)
    cur_filter.set_source(Source.pik)
    bot.reply_to(msg, sql_server.sales_all_today(), reply_markup=types.ReplyKeyboardHide())
    print_step_keyboard(msg, STATE_SOLD_ALL_TODAY)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_SOLD_ALL_YESTERDAY)
def sold_all_yesterday(msg):
    bot.reply_to(msg, STATE_SOLD_ALL_YESTERDAY, reply_markup=types.ReplyKeyboardHide())
    cur_filter = get_current_filter(msg.chat.id)
    cur_filter.set_time(Time.yesterday)
    cur_filter.set_source(Source.pik)
    print_step_keyboard(msg, STATE_SOLD_ALL_YESTERDAY)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_SOLD_REG_TODAY)
def sold_reg_today(msg):
    bot.reply_to(msg, STATE_SOLD_REG_TODAY, reply_markup=types.ReplyKeyboardHide())
    cur_filter = get_current_filter(msg.chat.id)
    if cur_filter.is_clear():
        cur_filter.set_time(Time.today)
        cur_filter.set_source(Source.regions)
    print_step_keyboard(msg, STATE_SOLD_REG_TODAY)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_SOLD_REG_YESTERDAY)
def sold_reg_yesterday(msg):
    bot.reply_to(msg, STATE_SOLD_REG_YESTERDAY, reply_markup=types.ReplyKeyboardHide())
    cur_filter = get_current_filter(msg.chat.id)
    if cur_filter.is_clear():
        cur_filter.set_time(Time.yesterday)
        cur_filter.set_source(Source.regions)
    print_step_keyboard(msg, STATE_SOLD_REG_YESTERDAY)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_SOLD_MOS_TODAY)
def sold_mos_today(msg):
    bot.reply_to(msg, STATE_SOLD_MOS_TODAY, reply_markup=types.ReplyKeyboardHide())
    cur_filter = get_current_filter(msg.chat.id)
    if cur_filter.is_clear():
        cur_filter.set_time(Time.today)
        cur_filter.set_source(Source.moscow)
    print_step_keyboard(msg, STATE_SOLD_MOS_TODAY)


@bot.message_handler(func=lambda msg: get_current_state(msg.chat.id) == STATE_SOLD_MOS_YESTERDAY)
def sold_mos_yesterday(msg):
    bot.reply_to(msg, STATE_SOLD_MOS_YESTERDAY, reply_markup=types.ReplyKeyboardHide())
    cur_filter = get_current_filter(msg.chat.id)
    if cur_filter.is_clear():
        cur_filter.set_time(Time.yesterday)
        cur_filter.set_source(Source.moscow)
    print_step_keyboard(msg, STATE_SOLD_MOS_YESTERDAY)


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
