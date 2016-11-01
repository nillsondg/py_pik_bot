import pyodbc

import config
from states import State
from states import Type


def get_sql_config(server, database):
    return "DRIVER={SQL Server};Server=" + server + ";DATABASE=" + database + \
           ";UID=" + config.UID + ";PWD=" + config.PWD + ";Trusted_Connection=Yes"


class SQL:
    sales_strings = {
        State.pik_today: "Продано {} м²",
        State.pik_yesterday: "Вчера продано {} м²",
        State.moscow_today: "В Московском регионе продано {} м²",
        State.moscow_yesterday: "Вчера в Московском регионе продано {} м²",
        State.regions_today: "В регионах продано {} м²",
        State.regions_yesterday: "Вчера в регионах продано  {} м²",
    }
    forecast_strings = {
        State.pik_today: "Потенциал {s}м² (подтверждены {ps}м²)",
        State.pik_yesterday: "Вчера потеницал {s}м² (подтверждены {ps}м²)",
        State.moscow_today: "Потенциал Московского региона {s}м² (подтверждены {ps}м²)",
        State.moscow_yesterday: "Вчера потеницал Московского региона {s}м² (подтверждены {ps}м²)",
        State.regions_today: "Потенциал регионов {s}м² (подтверждены {ps}м²)",
        State.regions_yesterday: "Вчера потенциал регионов {s}м² (подтверждены {ps}м²)",
    }
    sales_requests = {
        State.pik_today: "exec tele_bot_sold null",
        State.pik_yesterday: "exec tele_bot_sold null, -1",
        State.moscow_today: "exec tele_bot_sold 1",
        State.moscow_yesterday: "exec tele_bot_sold 1, -1",
        State.regions_today: "exec tele_bot_sold 0",
        State.regions_yesterday: "exec tele_bot_sold 0, -1",
    }
    forecast_requests = {
        State.pik_today:
            """declare @today date = cast(getdate() as date)
                select
                  sum(Potential.new_areaunderopportunity) as s
                , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
                from Potential
                where DateofQuery = @today
                  and EstimatedDateOfDeal = @today""",
        State.pik_yesterday:
            '''
                declare @today date = dateadd(day, -1, cast(getdate() as date))
                select
                  sum(Potential.new_areaunderopportunity) as s
                , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
                from Potential
                where DateofQuery = @today
                  and EstimatedDateOfDeal = @today
              '''
        ,
        State.moscow_today:
            '''
                declare @today date = cast(getdate() as date)
                select
                  sum(Potential.new_areaunderopportunity) as s
                , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
                from Potential
                where DateofQuery = @today
                  and EstimatedDateOfDeal = @today
                  and super_region = \'Москва и МО\'
              '''
        ,
        State.moscow_yesterday:
            '''
                declare @today date = dateadd(day, -1, cast(getdate() as date))
                select
                  sum(Potential.new_areaunderopportunity) as s
                , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
                from Potential
                where DateofQuery = @today
                  and EstimatedDateOfDeal = @today
                  and super_region = \'Москва и МО\'
              '''
        ,
        State.regions_today:
            '''
                declare @today date = cast(getdate() as date)
                select
                  sum(Potential.new_areaunderopportunity) as s
                , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
                from Potential
                where DateofQuery = @today
                  and EstimatedDateOfDeal = @today
                  and super_region = \'Регионы\'
              '''
        ,
        State.regions_yesterday:
            '''
                declare @today date = dateadd(day, -1, cast(getdate() as date))
                select
                  sum(Potential.new_areaunderopportunity) as s
                , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
                from Potential
                where DateofQuery = @today
                  and EstimatedDateOfDeal = @today
                  and super_region = \'Регионы\'
              '''
        ,
    }

    def __init__(self):
        self.pik_sales_local = pyodbc.connect(get_sql_config(config.SALES_SERVER, config.SALES_DATABASE))
        self.pik_mscrm_dw = pyodbc.connect(get_sql_config(config.MSCRM_SERVER, config.MSCRM_DATABASE))

    def request(self, state):
        if state.type == Type.sold:
            return self.request_sales(state)
        elif state.type == Type.forecast:
            return self.request_forecast(state)

    def request_sales(self, state):
        area = self.execute_sales(self.sales_requests[state])
        if area is None:
            return "Нет данных"
        return self.sales_strings[state].format(round(area, 2))

    def request_forecast(self, state):
        s, ps = self.execute_forecast(self.forecast_requests[state])
        if s is None:
            return "Нет данных"
        return self.forecast_strings[state].format(s=round(s, 2), ps=round(ps, 2))

    def execute_sales(self, sql):
        cursor = self.pik_sales_local.cursor()
        cursor.execute(sql)
        cursor.nextset()
        row = cursor.fetchone()
        cursor.close()
        if row:
            return row.areaSum
        else:
            return None

    def execute_forecast(self, sql):
        cursor = self.pik_mscrm_dw.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        if row:
            return row.s, row.ps
        else:
            return None
