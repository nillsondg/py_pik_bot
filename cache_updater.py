import sql
from states import *
import mongodb
import sched
import time
import logging
import asyncio
import datetime

logging.basicConfig(filename="cache_updater.log", level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
sql_server = sql.SQL()
mongo = mongodb.MongoDB()

s = sched.scheduler(time.time, time.sleep)
CACHE_TTL = 15 * 60


@asyncio.coroutine
def recaching():
    logging.info(datetime.datetime.now().strftime("%d-%m %H:%M:%S") + " start caching ")
    for state in State:
        yield from recaching2(state)


@asyncio.coroutine
def recaching2(state):
    try:
        logging.info(datetime.datetime.now().strftime("%d-%m %H:%M:%S") + " caching " + state.description)
        if state.type == Type.sms:
            data = sql_server.request_sms(state)
            mongo.cache(data, Type.sms, state)
        elif state.type == Type.sold:
            data = sql_server.request_sales(state)
            mongo.cache(data, Type.sold, state)
        elif state.type == Type.forecast:
            data = sql_server.request_forecast(state)
            mongo.cache(data, Type.forecast, state)
    except Exception as e:
        logging.error(e)
        print("Error!")
        print(e)


def recache(sc):
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(recaching())
    finally:
        event_loop.close()
    s.enter(CACHE_TTL, 1, recache, (sc,))


s.enter(0, 1, recache, (s,))
s.run()
