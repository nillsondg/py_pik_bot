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
            elif state.type == Type.sold:
                return morton_server.sold_request(state)
            elif state.type == Type.forecast:
                return morton_server.forecast_request(state)
        else:
            if state.type == Type.sms:
                last_cached_time = mongo.get_last_cached_time(state.type, state)
                if (last_cached_time is None
                        or datetime.datetime.now() - last_cached_time > datetime.timedelta(minutes=2)):
                    data = sql_server.request_sms(state)
                    mongo.cache(data, state.type, state)
                    return data, datetime.datetime.now()
                else:
                    return mongo.get_cache(state.type, state)["txt"], last_cached_time
            elif state.type == Type.sold:
                return sql_server.request_sales(state)
            elif state.type == Type.forecast:
                return sql_server.request_forecast(state)
