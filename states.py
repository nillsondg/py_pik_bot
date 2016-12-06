from enum import Enum


class Time(Enum):
    today = "Сегодня"
    yesterday = "Вчера"
    holidays = "Выходные"
    month = "Месяц"


class Source(Enum):
    pik = "ПИК"
    moscow = "Москва"
    regions = "Регионы"
    morton = "Мортон"


class Type(Enum):
    sold = "Продажи"
    forecast = "Прогноз"
    sms = "СМС"


class State(Enum):
    none = None, None, None
    auth = None, None, "auth"
    pik_today_sold = Source.pik, Time.today, Type.sold
    pik_yesterday_sold = Source.pik, Time.yesterday, Type.sold
    moscow_today_sold = Source.moscow, Time.today, Type.sold
    moscow_yesterday_sold = Source.moscow, Time.yesterday, Type.sold
    regions_today_sold = Source.regions, Time.today, Type.sold
    regions_yesterday_sold = Source.regions, Time.yesterday, Type.sold

    pik_today_forecast = Source.pik, Time.today, Type.forecast
    pik_yesterday_forecast = Source.pik, Time.yesterday, Type.forecast
    moscow_today_forecast = Source.moscow, Time.today, Type.forecast
    moscow_yesterday_forecast = Source.moscow, Time.yesterday, Type.forecast
    regions_today_forecast = Source.regions, Time.today, Type.forecast
    regions_yesterday_forecast = Source.regions, Time.yesterday, Type.forecast

    pik_today_sms = Source.pik, Time.today, Type.sms
    pik_yesterday_sms = Source.pik, Time.yesterday, Type.sms
    moscow_today_sms = Source.moscow, Time.today, Type.sms
    moscow_yesterday_sms = Source.moscow, Time.yesterday, Type.sms
    regions_today_sms = Source.regions, Time.today, Type.sms
    regions_yesterday_sms = Source.regions, Time.yesterday, Type.sms
    morton_today_sms = Source.morton, Time.today, Type.sms

    # morton_yesterday = (Source.morton, Time.yesterday)
    # morton_holidays = (Source.morton, Time.holidays)
    # morton_month = (Source.morton, Time.month)

    def __init__(self, source, time, type):
        self.source = source
        self.time = time
        self.type = type

    @property
    def description(self):
        if self.source is not None and self.time is not None:
            return self.source.value + " " + self.time.value
        return "none"

    @staticmethod
    def get_state_by_description(description, state_type):
        attr = description.split()
        if len(attr) != 2:
            return State.none
        source = attr[0]
        time = attr[1]
        try:
            if state_type is not None:
                state = State((Source(source), Time(time), state_type))
            else:
                state = State((Source(source), Time(time), Type.sold))
        except ValueError:
            state = State.none
        return state


class StateTransitions:
    transitions = {
        State.none: [],

        State.pik_today_sold: [State.moscow_today_sold, State.regions_today_sold, State.pik_yesterday_sold,
                               State.moscow_yesterday_sold, State.regions_yesterday_sold],

        State.pik_today_forecast: [State.moscow_today_forecast, State.regions_today_forecast,
                                   State.pik_yesterday_forecast,
                                   State.moscow_yesterday_forecast, State.regions_yesterday_forecast],
        State.pik_today_sms: [State.moscow_today_sms, State.regions_today_sms, State.pik_yesterday_sms,
                              State.moscow_yesterday_sms, State.regions_yesterday_sms, State.morton_today_sms],
    }

    @staticmethod
    def get_transition_for_state(state):
        try:
            transition = StateTransitions.transitions[state]
        except KeyError:
            transition = []
        return transition
