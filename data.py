import sql
from states import *
import mongodb
import datetime

sql_server = sql.SQL()
mongo = mongodb.MongoDB()
SECONDS_TO_MANUAL_RECACHE = 5


class DataProvider:
    @staticmethod
    def request_with_cache(state, last_request_time=None):
        if state.type == Type.sold:
            return DataProvider.__get_sold(state, last_request_time)
        elif state.type == Type.forecast:
            return DataProvider.__get_forecast(state, last_request_time)
        elif state.type == Type.sms:
            return DataProvider.__get_sms(state, last_request_time)

    @staticmethod
    def __get_sms(state, last_request_time):
        last_cached_time = mongo.get_last_cached_time(state.type, state)
        if (last_request_time is not None
            and datetime.datetime.now() - last_request_time < datetime.timedelta(
                seconds=SECONDS_TO_MANUAL_RECACHE)):
            data = sql_server.request_sms(state)
            mongo.cache(data, state.type, state)
            return data, datetime.datetime.now()
        else:
            return mongo.get_cache(state.type, state)["txt"], last_cached_time

    @staticmethod
    def __get_sold(state, last_request_time):
        last_cached_time = mongo.get_last_cached_time(state.type, state)
        return mongo.get_cache(state.type, state)["txt"], last_cached_time

    @staticmethod
    def __get_forecast(state, last_request_time):
        last_cached_time = mongo.get_last_cached_time(state.type, state)
        return mongo.get_cache(state.type, state)["txt"], last_cached_time
