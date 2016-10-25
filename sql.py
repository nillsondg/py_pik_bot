import pyodbc

import config


def get_sql_config(server, database):
    return "DRIVER={SQL Server};Server=" + server + ";DATABASE=" + database + \
           ";UID=" + config.UID + ";PWD=" + config.PWD + ";Trusted_Connection=Yes"


class SQL:
    def __init__(self):
        self.pik_sales_local = pyodbc.connect(get_sql_config(config.SALES_SERVER, config.SALES_DATABASE))
        self.pik_mscrm_dw = pyodbc.connect(get_sql_config(config.MSCRM_SERVER, config.MSCRM_DATABASE))

    def execute_sales(self, sql):
        cursor = self.pik_sales_local.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        if row:
            return row.sumArea
        else:
            return -1

    def sales_all_today(self):
        return self.execute_sales("exec tele_bot_sold null")

    def sales_all_yesterday(self):
        return self.execute_sales("exec tele_bot_sold null, -1")
