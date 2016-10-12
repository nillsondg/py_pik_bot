import telebot
import hashlib

token = "266702664:AAGe1ssRKsrCdsnPhcdXjeI0WM-CJIJ15sY"
bot = telebot.TeleBot(token)
users = []
auth_requested = False


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, "Это может помочь… или нет")


@bot.message_handler(func=lambda m: auth_requested)
def check_auth(message):
    if check_code(message.text):
        users.append(message.from_user.username)
        global auth_requested
        auth_requested = False
        bot.reply_to(message, "Добро пожаловать")
    else:
        bot.reply_to(message, "Неверно, попроуйте еще")


def check_code(code):
    return hashlib.md5(code.encode('utf-8')).hexdigest() == "bc250e0d83c37b0953ada14e7bbc1dfd"


@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda m: True)
def send_welcome(message):
    bot.reply_to(message, "Привет!")
    username = message.from_user.username
    if username not in users:
        bot.send_message(message.chat.id, "Введите кодовое слово")
        global auth_requested
        auth_requested = True


bot.polling()
