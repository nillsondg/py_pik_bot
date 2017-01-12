import datetime
import logging
from telebot import types

import server
from session import Session, User, Group
import auth
from data import DataProvider
from states import *

session = Session()
bot = server.init_bot()


# request construct
class Bot:
    SOLD_CMD = "sold"
    FORECAST_CMD = "forecast"
    SMS_CMD = "sms"

    @staticmethod
    @bot.message_handler(commands=['start'])
    def send_welcome(msg):
        if not session.check_user_id_in_db(msg.from_user.id):
            session.set_current_state(msg.chat.id, msg.from_user.id, State.auth)
            bot.send_message(msg.chat.id, "Введите кодовое слово")
            bot.register_next_step_handler(msg, Bot.check_auth)
        else:
            session.update_user_auth(msg.from_user)
            Bot.print_result_with_keyboard(msg, "Выберите команду")

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
            session.add_user(msg.chat.id, user)
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
            session.update_user_group(user)
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
    @bot.message_handler(func=lambda msg: msg.text == Source.all.value)
    def sms_all(msg):
        state = State.all_today_sms
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
        elif 'sold' in msg.text.lower():
            Bot.sold(msg)
            return
        elif 'forecast' in msg.text.lower():
            Bot.forecast(msg)
            return
        elif 'sms' in msg.text.lower():
            Bot.sms_all(msg)
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
        bot.send_message(msg.chat.id, text, reply_markup=types.ReplyKeyboardHide, disable_notification=True)

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
        if not session.check_user_id_in_db(msg.from_user.id):
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
            bot.send_message(msg.chat.id, RequestProcessor.format_cache_time(result[1]), disable_notification=True,
                             parse_mode="Markdown")
            Bot.print_result_with_keyboard(msg, result[0], next_step=next_step)
        else:
            Bot.print_result_with_keyboard(msg, result, next_step=next_step)

        return state

    @staticmethod
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
        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=False)
        markup.row(types.KeyboardButton(Source.pik.value), types.KeyboardButton(Source.morton.value),
                   types.KeyboardButton(Source.all.value))
        return markup

    @staticmethod
    def full_info_keyboard():
        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=False)
        markup.row(types.KeyboardButton(Type.sold.value), types.KeyboardButton(Type.forecast.value),
                   types.KeyboardButton(Type.sms.value))
        return markup


server.start_bot()
