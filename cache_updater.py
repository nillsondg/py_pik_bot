import sql
from states import *
import mongodb
import sched
import time
import logging

logging.basicConfig(filename="cache_updater.log", level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
sql_server = sql.SQL()
mongo = mongodb.MongoDB()

s = sched.scheduler(time.time, time.sleep)
CACHE_TTL = 15 * 60


def recache_sms(sc):
    try:
        data = sql_server.request_sms(State.morton_today)
        mongo.cache(data, Type.sms, State.morton_today)

        data = sql_server.request_sms(State.pik_today)
        mongo.cache(data, Type.sms, State.pik_today)
    except Exception as e:
        logging.error(e)
        print("Error!")
        print(e)
    s.enter(CACHE_TTL, 1, recache_sms, (sc,))

s.enter(0, 1, recache_sms, (s,))
s.run()
