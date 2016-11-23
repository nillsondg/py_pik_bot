import sql
import morton
from states import *
import mongodb
import sched
import time
import os

os.environ['NO_PROXY'] = 'https://webapi.morton.ru'

sql_server = sql.SQL()
morton_server = morton.Morton()
mongo = mongodb.MongoDB()

s = sched.scheduler(time.time, time.sleep)
TWENTY_MINUTES_IN_SECONDS = 72000


def recache_sms(sc):
    try:
        data = morton_server.sms_request(State.morton_today)
        mongo.cache(data, Type.sms, State.pik_today)

        data = sql_server.request_sms(State.pik_today)
        mongo.cache(data, Type.sms, State.morton_today)
    except Exception as e:
        # todo log
        print("Error!")
        print(e)
    s.enter(TWENTY_MINUTES_IN_SECONDS, 1, recache_sms, (sc,))

s.enter(0, 1, recache_sms, (s,))
s.run()