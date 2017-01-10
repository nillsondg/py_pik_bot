import telebot
import cherrypy
import os
import logging
import datetime
from config import TOKEN, ENV

os.environ['NO_PROXY'] = 'https://api.telegram.org'
WEBHOOK_HOST = 'tgbot.pik.ru'
WEBHOOK_PORT = 443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % TOKEN

bot = None


def init_bot():
    global bot
    bot = telebot.TeleBot(TOKEN)
    bot.set_update_listener(listener)
    bot.remove_webhook()
    _init_logger()

    print("inited bot")
    return bot


def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)
            logging.info(datetime.datetime.now().strftime("%d-%m %H:%M:%S") + " " + str(m.chat.first_name) + " [" + str(
                m.chat.id) + "]: " + m.text)


def _init_logger():
    logging.basicConfig(filename="bot.log", format='[%(asctime)s] %(message)s')
    logging.getLogger().addHandler(logging.StreamHandler())
    telebot.logger.setLevel(logging.INFO)


def start_bot():
    global bot

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

    if ENV == "prod":
        bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

        cherrypy.config.update({
            'server.socket_host': WEBHOOK_LISTEN,
            'server.socket_port': WEBHOOK_PORT
        })
        cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
    else:
        bot.polling()

    print("started bot")
