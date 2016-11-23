import sql
import morton
from states import *
import mongodb
import datetime

sql_server = sql.SQL()
morton_server = morton.Morton()
mongo = mongodb.MongoDB()


class DataProvider:
    @staticmethod
    def request(state):
        if state.source == Source.morton:
            if state.type == Type.sms:
                return morton_server.sms_request(state)
        else:
            if state.type == Type.sms:
                return sql_server.request_sms(state)

    @staticmethod
    def request_with_cache(state, last_request_time):
        if state.source == Source.morton:
            if state.type == Type.sms:
                last_cached_time = mongo.get_last_cached_time(state.type, state)
                if (last_request_time is not None
                        and datetime.datetime.now() - last_request_time < datetime.timedelta(seconds=20)):
                    data = morton_server.sms_request(state)
                    mongo.cache(data, state.type, state)
                    return data, datetime.datetime.now()
                else:
                    return mongo.get_cache(state.type, state)["txt"], last_cached_time
        else:
            if state.type == Type.sms:
                last_cached_time = mongo.get_last_cached_time(state.type, state)
                if (last_request_time is not None
                        and datetime.datetime.now() - last_request_time < datetime.timedelta(seconds=20)):
                    data = sql_server.request_sms(state)
                    mongo.cache(data, state.type, state)
                    return data, datetime.datetime.now()
                else:
                    return mongo.get_cache(state.type, state)["txt"], last_cached_time
