import config
import requests
from states import *
from datetime import datetime, timedelta


class Morton:
    host = 'https://webapi.morton.ru'

    sms_path = "/objects/mortonnew"
    old_path = '/objects/smssalesmorton'
    sold_path = '/objects/mortonstat'

    date = {
        State.morton_today: 'today',
        State.morton_yesterday: 'yesterday',
        State.morton_holidays: 'weekend',
        State.morton_month: 'month',
    }
    sales_strings = {
        State.morton_today: "Продано в Мортон {} м²",
        State.morton_yesterday: "Вчера продано в Мортон {} м²"
    }

    def forecast_request(self, state):
        return 'Нет данных по потецниалу Мортон'

    def sms_request(self, state):
        data = self.request(self.sms_path)
        if data is None:
            return 'Не могу подключиться к Мортон'
        for i in data:
            if i["tp"] == self.date[state]:
                return self.format_sms(i["txt"])
        return None

    def format_sms(self, txt):
        txt = txt.replace("Отчет за", 'Контрактация за')
        txt = txt.replace("Отчёт за", 'Контрактация за')
        return txt

    def old_request(self, state):
        data = self.request(self.old_path)
        if data is None:
            return 'Не могу подключиться к Мортон'
        for i in data:
            if i["tp"] == self.date[state]:
                return self.format_old(i["txt"])
        return None

    def format_old(self, txt):
        return txt.replace("Отчет за", 'Контрактация за')

    def sold_request(self, state):
        data = self.request(self.sold_path)
        if data is None:
            return 'Не могу подключиться к Мортон'
        today = datetime.now()
        yesterday = datetime.now() - timedelta(days=1)
        if state == state.morton_today:
            return self.sales_strings[state].format(self.sum_sold(data, today.day))
        elif state == state.morton_yesterday:
            return self.sales_strings[state].format(self.sum_sold(data, yesterday.day))
        return None

    def sum_sold(self, data, day):
        result = 0.00
        for i in data:
            if i["day"] == day:
                result += i["area"]
        return round(result, 2)

    def request(self, path):
        payload = {'token': config.MORTON_TOKEN}
        header = {'Accept': "application"}
        r = requests.get(self.host + path, params=payload, header=header)
        if r.status_code != requests.codes.ok:
            return None
        return r.json()["data"]