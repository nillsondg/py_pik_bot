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
        area = self.__execute_sales(sales_requests[state])
        if area is None:
            return "Нет данных"
        return sales_strings[state].format(round(area, 2))

    def request_forecast(self, state):
        s, ps = self.__execute_forecast(forecast_requests[state])
        if s is None:
            return "Нет данных"
        return forecast_strings[state].format(s=round(s, 2), ps=round(ps, 2))

    def request_sms(self, state):
        return self.__execute_sms(sms_requests[state])

    def __execute_sales(self, sql):
        connection = self.get_pik_sales_local()
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            cursor.nextset()  # особенность запроса
            row = cursor.fetchone()
            if row:
                return row.areaSum
            else:
                return None
        finally:
            cursor.close()
            connection.close()

    def __execute_forecast(self, sql):
        connection = self.get_pik_mscrm_dw()
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            row = cursor.fetchone()
            if row:
                return row.s, row.ps
            else:
                return None
        finally:
            cursor.close()
            connection.close()

    def __execute_sms(self, sql):
        connection = self.get_pik_sales_local()
        cursor = connection.cursor()
        try:
            row = None
            cursor.execute(sql)
            while cursor.nextset():
                try:
                    row = cursor.fetchone()
                    break
                except pyodbc.ProgrammingError as e:
                    pass
            if row:
                return row.txt
            else:
                return "Нет продаж"
        finally:
            cursor.close()
            connection.close()
