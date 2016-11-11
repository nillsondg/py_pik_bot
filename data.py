import sql
from states import *
sql_server = sql.SQL()


class DataProvider:
    @staticmethod
    def request(state):
        if state.source == Source.morton:
            return "not implemented"
        elif state.source == Source.sms:
            return sql_server.request_sms(state)
        else:
            if state.type == Type.sold:
                return sql_server.request_sales(state)
            elif state.type == Type.forecast:
                return sql_server.request_forecast(state)

