import datetime
import logging
import os

import cherrypy
import telebot
from telebot import types

import auth
import mongodb
from config import TOKEN, ENV
from data import DataProvider
from states import *

os.environ['NO_PROXY'] = 'https://api.telegram.org'
WEBHOOK_HOST = 'tgbot.pik.ru'
WEBHOOK_PORT = 443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % TOKEN

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
    _users = dict()

    def get_user(self, uid, user_id):
        if uid not in self._users:
            if not mongo.check_user_id_in_db(user_id):
                self._users[uid] = User()
            else:
                mongo_user = mongo.get_user_from_db(user_id)
                self._users[uid] = User.create_user_from_mongo(mongo_user)
        return self._users[uid]

    def get_user_with_msg(self, msg):
        uid = msg.chat.id
        tg_user = msg.from_user
        if uid not in self._users:
            if not mongo.check_user_id_in_db(tg_user.id):
                self._users[uid] = User.create_user_from_telegram(tg_user)
            else:
                mongo_user = mongo.get_user_from_db(tg_user.id)
                self._users[uid] = User.create_user_from_mongo(mongo_user)
        return self._users[uid]

    def add_user(self, uid, user):
        mongo.add_user_into_db(user)
        self._users[uid] = user

    def get_current_state(self, uid, user_id):
        return self.get_user(uid, user_id).state

    def set_current_state(self, uid, user_id, state):
        self.get_user(uid, user_id).state = state

    def get_user_last_state(self, uid, user_id):
        return self.get_user(uid, user_id).last_state

    def set_user_last_state(self, uid, user_id, state):
        self.get_user(uid, user_id).last_state = state

    def get_last_request_time(self, uid, user_id):
        return self.get_user(uid, user_id).last_request_time

    def set_last_request_time_now(self, uid, user_id):
        self.get_user(uid, user_id).last_request_time = datetime.datetime.now()

    @staticmethod
    def is_user_in_full_info_group(uid, user_id):
        return session.get_user(uid, user_id).group == Group.full_info

    @staticmethod
    def is_user_in_sms_only_group(uid, user_id):
        return session.get_user(uid, user_id).group == Group.sms_only


session = Session()
mongo = mongodb.MongoDB()


# request construct
class Bot:
    SOLD_CMD = "sold"
    FORECAST_CMD = "forecast"
    SMS_CMD = "sms"

    @staticmethod
    @bot.message_handler(commands=['start'])
    def send_welcome(msg):
        if not mongo.check_user_id_in_db(msg.from_user.id):
            session.set_current_state(msg.chat.id, msg.from_user.id, State.auth)
            bot.send_message(msg.chat.id, "Введите кодовое слово")
            bot.register_next_step_handler(msg, Bot.check_auth)
        else:
            mongo.update_user_auth(msg.from_user)
            Bot.print_result_with_keyboard(msg, "Введите команду")

    @staticmethod
    @bot.message_handler(commands=['ok'])
    def ok(msg):
        Bot.print_result_with_keyboard(msg, "Ok")

    @staticmethod
    @bot.message_handler(commands=['refresh'])
    def refresh_keyboard(msg):
        Bot.print_result_with_keyboard(msg, "Клавиатура обновлена")

    @staticmethod
    @bot.message_handler(commands=['regroup'])
    def change_group(msg):
        print("change_group")
        session.set_current_state(msg.chat.id, msg.from_user.id, State.auth)
        bot.send_message(msg.chat.id, "Введите кодовое слово")
        bot.register_next_step_handler(msg, Bot.check_regroup)

    @staticmethod
    def check_auth(msg):
        user = User.create_user_from_telegram(msg.from_user)
        group = auth.check_code_and_return_group(msg.text)
        if group is not None:
            mongo.add_user_into_db(user)
            Bot.print_result_with_keyboard(msg, "Добро пожаловать")
            session.set_current_state(msg.chat.id, msg.from_user.id, State.none)
        else:
            bot.reply_to(msg, "Неверно, попробуйте еще", disable_notification=True)
            bot.register_next_step_handler(msg, Bot.check_auth)

    @staticmethod
    def check_regroup(msg):
        user = session.get_user(msg.chat.id, msg.from_user.id)
        group = auth.check_code_and_return_group(msg.text)
        if group is not None:
            mongo.update_user_group(user)
            Bot.print_result_with_keyboard(msg, "Группа изменена")
        else:
            bot.reply_to(msg, "Неверно, попробуйте еще", disable_notification=True)
        session.set_current_state(msg.chat.id, msg.from_user.id, State.none)

    @staticmethod
    @bot.message_handler(commands=[SOLD_CMD])
    @bot.message_handler(func=lambda msg: msg.text == Type.sold.value)
    def sold(msg):
        state = State.pik_today_sold
        RequestProcessor.handle_request(msg, state)

    @staticmethod
    @bot.message_handler(commands=[FORECAST_CMD])
    @bot.message_handler(func=lambda msg: msg.text == Type.forecast.value)
    def forecast(msg):
        state = State.pik_today_forecast
        RequestProcessor.handle_request(msg, state)

    @staticmethod
    @bot.message_handler(commands=[SMS_CMD])
    @bot.message_handler(func=lambda msg: msg.text == Type.sms.value)
    def sms(msg):
        state = State.pik_today_sms
        RequestProcessor.handle_request(msg, state)

    @staticmethod
    @bot.message_handler(func=lambda msg: msg.text == Source.pik.value)
    def sms_pik(msg):
        if not session.is_user_in_sms_only_group(msg.chat.id, msg.from_user.id):
            return
        state = State.pik_today_sms
        RequestProcessor.handle_request(msg, state, next_step=False)

    @staticmethod
    @bot.message_handler(func=lambda msg: msg.text == Source.morton.value)
    def sms_morton(msg):
        if not session.is_user_in_sms_only_group(msg.chat.id, msg.from_user.id):
            return
        state = State.morton_today_sms
        RequestProcessor.handle_request(msg, state, next_step=False)

    @staticmethod
    @bot.message_handler(func=lambda msg: session.get_current_state(msg.chat.id, msg.from_user.id) == State.none)
    def get_message(msg):
        if msg.text == "Назад":
            Bot.ok(msg)
            return
        last_state = session.get_user_last_state(msg.chat.id, msg.from_user.id)
        state = State.get_state_by_description(msg.text, last_state.type)
        if state == State.none:
            Bot.print_result_with_keyboard(msg, "Неверный запрос")
            return
        RequestProcessor.handle_request(msg, state)

    @staticmethod
    def print_result_with_keyboard(msg, text, next_step=False):
        print("print_keyboard")
        user = session.get_user(msg.chat.id, msg.from_user.id)
        if next_step:
            Bot.print_step_keyboard(msg, text)
        elif user.group == Group.full_info:
            Bot.print_full_info_keyboard(msg, text)
        elif user.group == Group.sms_only:
            Bot.print_sms_keyboard(msg, text)
        else:
            Bot.hide_keyboard(msg, text)

    @staticmethod
    def print_sms_keyboard(msg, text):
        print("print_sms_keyboard")
        bot.send_message(msg.chat.id, text, reply_markup=KeyboardCreator.sms_keyboard(), disable_notification=True)

    @staticmethod
    def print_full_info_keyboard(msg, text):
        print("print_full_info_keyboard")
        bot.send_message(msg.chat.id, text, reply_markup=KeyboardCreator.full_info_keyboard(),
                         disable_notification=True)

    @staticmethod
    def hide_keyboard(msg, text):
        print("hide_keyboard")
        bot.send_message(msg.chat.id, text, reply_markup=types.ReplyKeyboardRemove, disable_notification=True)

    @staticmethod
    def print_step_keyboard(msg, text):
        print("print_step_keyboard")
        user = session.get_user(msg.chat.id, msg.from_user.id)
        markup = KeyboardCreator.step_keyboard(user)
        if markup is None:
            session.set_current_state(msg.chat.id, msg.from_user.id, State.none)
            Bot.print_result_with_keyboard(msg, text)
            return
        bot.send_message(msg.chat.id, text, reply_markup=markup, disable_notification=True)


class RequestProcessor:
    @staticmethod
    def handle_request(msg, state, next_step=True):
        if not mongo.check_user_id_in_db(msg.from_user.id):
            session.set_current_state(msg.chat.id, msg.from_user.id, State.auth)
            bot.send_message(msg.chat.id, "Вы не авторизованы. Введите кодовое слово")
            bot.register_next_step_handler(msg, Bot.check_auth)
            return

        current_state = session.get_current_state(msg.chat.id, msg.from_user.id)

        # switch to prevent next request before first done
        if current_state != State.none:
            return
        else:
            session.set_current_state(msg.chat.id, msg.from_user.id, state)

        print("current state = " + session.get_current_state(msg.chat.id, msg.from_user.id).description)
        result_state = RequestProcessor.process_request_and_return_state(msg, state, next_step)
        session.set_current_state(msg.chat.id, msg.from_user.id, State.none)
        session.set_last_request_time_now(msg.chat.id, msg.from_user.id)
        session.set_user_last_state(msg.chat.id, msg.from_user.id, result_state)

    @staticmethod
    def process_request_and_return_state(msg, state, next_step):
        bot.send_chat_action(msg.chat.id, 'typing')
        result = "Произошла ошибка"
        last_state = session.get_user_last_state(msg.chat.id, msg.from_user.id)
        if last_state.type is not None:
            print(last_state.type.value)
        print(state.type.value)
        try:
            if last_state == state:
                result = DataProvider.request_with_cache(state,
                                                         session.get_last_request_time(msg.chat.id, msg.from_user.id))
            else:
                result = DataProvider.request_with_cache(state)
        except Exception as e:
            logging.error(e)
            print("ERROR!")
            print(e)
            state = State.none
            next_step = False

        if isinstance(result, (list, tuple)):
            bot.send_message(msg.chat.id, format_cache_time(result[1]), disable_notification=True,
                             parse_mode="Markdown")
            Bot.print_result_with_keyboard(msg, result[0], next_step=next_step)
        else:
            Bot.print_result_with_keyboard(msg, result, next_step=next_step)

        return state


def format_cache_time(date_time):
    # cause server incorrect time
    date_time -= datetime.timedelta(hours=1)
    return "_@" + date_time.strftime("%H:%M:%S") + "_"


class KeyboardCreator:
    @staticmethod
    def step_keyboard(user):
        markup = types.ReplyKeyboardMarkup()
        next_states = StateTransitions.get_transition_for_state(user.state)
        if len(next_states) == 0:
            return None
        for next_state in next_states:
            markup.add(types.KeyboardButton(next_state.description))
        markup.add(types.KeyboardButton("Назад"))
        return markup

    @staticmethod
    def sms_keyboard():
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
        markup.row(types.KeyboardButton(Source.pik.value), types.KeyboardButton(Source.morton.value))
        return markup

    @staticmethod
    def full_info_keyboard():
        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=False)
        markup.row(types.KeyboardButton(Type.sold.value), types.KeyboardButton(Type.forecast.value),
                   types.KeyboardButton(Type.sms.value))
        return markup


# only used for console output now
def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)


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

bot.set_update_listener(listener)
bot.remove_webhook()
if ENV == "prod":
    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

    cherrypy.config.update({
        'server.socket_host': WEBHOOK_LISTEN,
        'server.socket_port': WEBHOOK_PORT
    })
    cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
else:
    bot.polling()
