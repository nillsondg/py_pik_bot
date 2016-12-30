import datetime

import mongodb
import sql
from states import *

sql_server = sql.SQL()
mongo = mongodb.MongoDB()
SECONDS_TO_MANUAL_RECACHE = 5


class DataProvider:
    @staticmethod
    def request_with_cache(state, last_request_time=None):
        if state.type == Type.sold:
            return DataProvider._get_sold(state, last_request_time)
        elif state.type == Type.forecast:
            return DataProvider._get_forecast(state, last_request_time)
        elif state.type == Type.sms:
            return DataProvider._get_sms(state, last_request_time)

    @staticmethod
    def _get_sms(state, last_request_time):
        last_cached_time = mongo.get_last_cached_time(state.type, state)
        cache = mongo.get_cache(state.type, state)
        if (cache is None or (last_request_time is not None
            and datetime.datetime.now() - last_request_time < datetime.timedelta(
                seconds=SECONDS_TO_MANUAL_RECACHE))):
            data = sql_server.request_sms(state)
            mongo.cache(data, state.type, state)
            print("recached")
            return data, datetime.datetime.now()
        else:
            print("from cache")
            return mongo.get_cache(state.type, state)["txt"], last_cached_time

    @staticmethod
    def _get_sold(state, last_request_time):
        last_cached_time = mongo.get_last_cached_time(state.type, state)
        cache = mongo.get_cache(state.type, state)
        if cache is None or datetime.datetime.now() - last_cached_time > datetime.timedelta(minutes=20):
            data = sql_server.request_sales(state)
            mongo.cache(data, state.type, state)
            return data, datetime.datetime.now()
        else:
            print("from cache")
            return cache["txt"], last_cached_time

    @staticmethod
    def _get_forecast(state, last_request_time):
        last_cached_time = mongo.get_last_cached_time(state.type, state)
        cache = mongo.get_cache(state.type, state)
        if cache is None or datetime.datetime.now() - last_cached_time > datetime.timedelta(minutes=20):
            data = sql_server.request_forecast(state)
            mongo.cache(data, state.type, state)
            print("recached")
            return data, datetime.datetime.now()
        else:
            print("from cache")
            return cache["txt"], last_cached_time
