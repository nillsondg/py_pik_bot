import pyodbc

import config
from sqlqueries import *


def get_sql_config(server, database):
    return "DRIVER={SQL Server};Server=" + server + ";DATABASE=" + database + \
           ";UID=" + config.UID + ";PWD=" + config.PWD + ";Trusted_Connection=Yes"


class SQL:

    def get_pik_sales_local(self):
        return pyodbc.connect(get_sql_config(config.SALES_SERVER, config.SALES_DATABASE))

    def get_pik_mscrm_dw(self):
        return pyodbc.connect(get_sql_config(config.MSCRM_SERVER, config.MSCRM_DATABASE))

    def request_sales(self, state):
        area = self.execute_sales(sales_requests[state])
        if area is None:
            return "Нет данных"
        return sales_strings[state].format(round(area, 2))

    def request_forecast(self, state):
        s, ps = self.execute_forecast(forecast_requests[state])
        if s is None:
            return "Нет данных"
        return forecast_strings[state].format(s=round(s, 2), ps=round(ps, 2))

    def request_sms(self, state):
        return self.execute_sms(sms_requests[state])

    def execute_sales(self, sql):
        connection = self.get_pik_sales_local()
        cursor = connection.cursor()
        cursor.execute(sql)
        cursor.nextset()  # особенность запроса
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        if row:
            return row.areaSum
        else:
            return None

    def execute_forecast(self, sql):
        connection = self.get_pik_mscrm_dw()
        cursor = connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        if row:
            return row.s, row.ps
        else:
            return None

    def execute_sms(self, sql):
        connection = self.get_pik_mscrm_dw()
        cursor = connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        if row:
            return row.txt
        else:
            return None
