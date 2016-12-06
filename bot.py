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
logging.basicConfig(filename="bot.log")
logging.getLogger().addHandler(logging.StreamHandler())
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(TOKEN)


class Group(Enum):
    sms_only = "sms_only"
    full_info = "full_info"


class User:
    state = State.none
    last_state = State.none
    last_request_time = None
    group = None

    @staticmethod
    def create_user_from_telegram(tg_user):
        user = User()
        user.id = tg_user.id
        user.last_name = tg_user.last_name
        user.first_name = tg_user.first_name
        user.username = tg_user.username
        return user

    @staticmethod
    def create_user_from_mongo(mongo_user):
        user = User()
        user.id = mongo_user["_id"]
        user.last_name = mongo_user["last_name"]
        user.first_name = mongo_user["first_name"]
        user.username = mongo_user["username"]
        user.group = Group(mongo_user["group"])
        return user


class Session:
    __users = dict()

    def get_user(self, uid):
        if uid not in self.__users:
            if not mongo.check_user_id_in_db(uid):
                self.__users[uid] = User()
            else:
                mongo_user = mongo.get_user_from_db(uid)
                self.__users[uid] = User.create_user_from_mongo(mongo_user)
        return self.__users[uid]

    def add_user(self, uid, user):
        mongo.add_user_into_db(user)
        self.__users[uid] = user

    def get_current_state(self, uid):
        return self.get_user(uid).state

    def set_current_state(self, uid, state):
        self.get_user(uid).state = state

    def get_user_last_state(self, uid):
        return self.get_user(uid).last_state

    def set_user_last_state(self, uid, state):
        self.get_user(uid).last_state = state

    def get_last_request_time(self, uid):
        return self.get_user(uid).last_request_time

    def set_last_request_time_now(self, uid):
        self.get_user(uid).last_request_time = datetime.datetime.now()


SOLD_CMD = "sold"
FORECAST_CMD = "forecast"
SMS_CMD = "sms"
mongo = mongodb.MongoDB()
session = Session()


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


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not mongo.check_user_id_in_db(message.from_user.id):
        session.set_current_state(message.chat.id, State.auth)
        bot.send_message(message.chat.id, "Введите кодовое слово")
        bot.register_next_step_handler(message, check_auth)
    else:
        mongo.update_user_auth(message.from_user)
        print_keyboard(message, "Введите команду")


def check_auth(msg):
    user = User.create_user_from_telegram(msg.from_user)
    if check_code_and_set_group(msg.text, user):
        mongo.add_user_into_db(user)
        print_keyboard(msg, "Добро пожаловать")
        session.set_current_state(msg.chat.id, State.none)
    else:
        bot.reply_to(msg, "Неверно, попробуйте еще", disable_notification=True)
        bot.register_next_step_handler(msg, check_auth)


@bot.message_handler(commands=['ok'])
def ok(msg):
    print_keyboard(msg, "Ok")


@bot.message_handler(commands=['refresh'])
def refresh_keyboard(msg):
    print_keyboard(msg, "Клавиатура обновлена")


@bot.message_handler(commands=['regroup'])
def change_group(msg):
    print("change_group")
    session.set_current_state(msg.chat.id, State.auth)
    bot.send_message(msg.chat.id, "Введите кодовое слово")
    bot.register_next_step_handler(msg, check_regroup)


def check_regroup(msg):
    user = session.get_user(msg.chat.id)
    if check_code_and_set_group(msg.text, user):
        mongo.update_user_group(user)
        print_keyboard(msg, "Группа изменена")
        session.set_current_state(msg.chat.id, State.none)


def check_code_and_set_group(code, user):
    if hashlib.md5(code.encode('utf-8')).hexdigest() == "bc250e0d83c37b0953ada14e7bbc1dfd":
        user.group = Group.full_info
        return True
    elif hashlib.md5(code.encode('utf-8')).hexdigest() == "70dda5dfb8053dc6d1c492574bce9bfd":
        user.group = Group.sms_only
        return True
    else:
        return False


def is_user_in_full_info_group(uid):
    return session.get_user(uid).group == Group.full_info


def is_user_in_sms_only_group(uid):
    return session.get_user(uid).group == Group.sms_only


@bot.message_handler(commands=[SOLD_CMD])
@bot.message_handler(func=lambda msg: msg.text == Type.sold.value)
def sold(msg):
    # last_state = session.get_user_last_state(msg.chat.id)
    # if last_state != State.none and last_state.type != Type.sold:
    #     state = State((last_state.source, last_state.time, Type.sold))
    # else:
    state = State.pik_today_sold
    handle_cmd(msg, state)


@bot.message_handler(commands=[FORECAST_CMD])
@bot.message_handler(func=lambda msg: msg.text == Type.forecast.value)
def forecast(msg):
    # last_state = session.get_user_last_state(msg.chat.id)
    # if last_state != State.none and last_state.type != Type.forecast:
    #     state = State((last_state.source, last_state.time, Type.forecast))
    # else:
    state = State.pik_today_forecast
    handle_cmd(msg, state)


@bot.message_handler(commands=[SMS_CMD])
@bot.message_handler(func=lambda msg: msg.text == Type.sms.value)
def sms(msg):
    # last_state = session.get_user_last_state(msg.chat.id)
    # if last_state != State.none and last_state.type != Type.sms:
    #     state = State((last_state.source, last_state.time, Type.sms))
    # else:
    state = State.pik_today_sms
    handle_cmd(msg, state)


@bot.message_handler(func=lambda msg: msg.text == Source.pik.value)
def sms_pik(msg):
    if not is_user_in_sms_only_group(msg.chat.id):
        return
    state = State.pik_today_sms
    handle_cmd(msg, state, next_step=False)


@bot.message_handler(func=lambda msg: msg.text == Source.morton.value)
def sms_morton(msg):
    if not is_user_in_sms_only_group(msg.chat.id):
        return
    state = State.morton_today_sms
    handle_cmd(msg, state, next_step=False)


@bot.message_handler(func=lambda msg: session.get_current_state(msg.chat.id) == State.none)
def get_message(msg):
    last_state = session.get_user_last_state(msg.chat.id)
    state = State.get_state_by_description(msg.text, last_state.type)
    if state == State.none:
        print_keyboard(msg, "Неверный запрос")
        return
    handle_cmd(msg, state)


def handle_cmd(msg, state, next_step=True):
    if not mongo.check_user_id_in_db(msg.from_user.id):
        check_auth(msg)
        return

    current_state = session.get_current_state(msg.chat.id)

    # switch to prevent next request before first done
    if current_state != State.none:
        return
    else:
        session.set_current_state(msg.chat.id, state)

    print("current state = " + session.get_current_state(msg.chat.id).description)
    result_state = process_request_and_return_state(msg, state, next_step)
    session.set_current_state(msg.chat.id, State.none)
    session.set_last_request_time_now(msg.chat.id)
    session.set_user_last_state(msg.chat.id, result_state)


def process_request_and_return_state(msg, state, next_step):
    bot.send_chat_action(msg.chat.id, 'typing')
    result = "Произошла ошибка"
    last_state = session.get_user_last_state(msg.chat.id)
    if last_state.type is not None:
        print(last_state.type.value)
    print(state.type.value)
    try:
        if last_state == state:
            # result = DataProvider.request_with_cache(state, session.get_last_request_time(msg.chat.id))
            result = "recached"
        else:
            # result = DataProvider.request_with_cache(state)
            result = "cached"
    except Exception as e:
        logging.error(e)
        print("ERROR!")
        print(e)
        state = State.none

    if isinstance(result, (list, tuple)):
        bot.send_message(msg.chat.id, format_cache_time(result[1]), disable_notification=True, parse_mode="Markdown")
        print_keyboard(msg, result[0], next_step=next_step)
    else:
        print_keyboard(msg, result, next_step=next_step)

    return state


def format_cache_time(date_time):
    # cause server incorrect time
    date_time -= datetime.timedelta(hours=1)
    return "_@" + date_time.strftime("%H:%M:%S") + "_"


def print_keyboard(msg, text, next_step=False):
    print("print_keyboard")
    user = session.get_user(msg.chat.id)
    if next_step:
        print_step_keyboard(msg, text)
    elif user.group == Group.full_info:
        print_full_info_keyboard(msg, text)
    elif user.group == Group.sms_only:
        print_sms_keyboard(msg, text)
    else:
        hide_keyboard(msg, text)


def print_sms_keyboard(msg, text):
    print("print_sms_keyboard")
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    markup.row(types.KeyboardButton(Source.pik.value), types.KeyboardButton(Source.morton.value))
    bot.send_message(msg.chat.id, text, reply_markup=markup, disable_notification=True)


def print_full_info_keyboard(msg, text):
    print("print_full_info_keyboard")
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=False)
    markup.row(types.KeyboardButton(Type.sold.value), types.KeyboardButton(Type.forecast.value),
               types.KeyboardButton(Type.sms.value))
    bot.send_message(msg.chat.id, text, reply_markup=markup, disable_notification=True)


def hide_keyboard(msg, text):
    print("hide_keyboard")
    bot.send_message(msg.chat.id, text, reply_markup=types.ReplyKeyboardHide(), disable_notification=True)


def print_step_keyboard(msg, text):
    print("print_step_keyboard")
    user = session.get_user(msg.chat.id)
    # if user.group != Group.full_info:
    #     print_keyboard(msg, text)
    #     return
    markup = types.ReplyKeyboardMarkup()
    next_states = StateTransitions.get_transition_for_state(user.state)
    if len(next_states) == 0:
        session.set_current_state(msg.chat.id, State.none)
        print_keyboard(msg, text)
        return
    for next_state in next_states:
        markup.add(types.KeyboardButton(next_state.description))
    bot.send_message(msg.chat.id, text, reply_markup=markup, disable_notification=True)


# only used for console output now
def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)


bot.set_update_listener(listener)
bot.remove_webhook()
# bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT
})
# cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})

bot.polling()
