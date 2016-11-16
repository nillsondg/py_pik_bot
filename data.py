import sql
import morton
from states import *
sql_server = sql.SQL()
morton_server = morton.Morton()


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

        elif state.source == Source.sms:
            return sql_server.request_sms(state)
        else:
            if state.type == Type.sold:
                return sql_server.request_sales(state)
            elif state.type == Type.forecast:
                return sql_server.request_forecast(state)

