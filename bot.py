import telebot
import cherrypy
import hashlib

API_TOKEN = "266702664:AAGe1ssRKsrCdsnPhcdXjeI0WM-CJIJ15sY"

WEBHOOK_HOST = 'tgbot.pik.ru'
WEBHOOK_PORT = 443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = 'tgbot.pik.ru'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_TOKEN)

print(WEBHOOK_URL_BASE)
print(WEBHOOK_URL_PATH)
bot = telebot.TeleBot(API_TOKEN)
users = []
auth_requested = False


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



# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()


# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))


# Start cherrypy server
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})


cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
