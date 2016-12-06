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
    none = None, None
    auth = ("auth", "auth")
    pik_today = (Source.pik, Time.today)
    pik_yesterday = (Source.pik, Time.yesterday)
    pik_holidays = (Source.pik, Time.holidays)
    pik_month = (Source.pik, Time.month)

    moscow_today = (Source.moscow, Time.today)
    moscow_yesterday = (Source.moscow, Time.yesterday)
    moscow_holidays = (Source.moscow, Time.holidays)
    moscow_month = (Source.moscow, Time.month)

    regions_today = (Source.regions, Time.today)
    regions_yesterday = (Source.regions, Time.yesterday)
    regions_holidays = (Source.regions, Time.holidays)
    regions_month = (Source.regions, Time.month)

    morton_today = (Source.morton, Time.today)
    morton_yesterday = (Source.morton, Time.yesterday)
    morton_holidays = (Source.morton, Time.holidays)
    morton_month = (Source.morton, Time.month)

    def __init__(self, source, time):
        self.source = source
        self.time = time
        self.type = Type.sold

    @property
    def description(self):
        if self.source is not None and self.time is not None:
            return self.source.value + " " + self.time.value
        return "none"

    @staticmethod
    def get_state_by_description(description):
        attr = description.split()
        if len(attr) != 2:
            return State.none
        source = attr[0]
        time = attr[1]
        try:
            state = State((Source(source), Time(time)))
        except ValueError:
            state = State.none
        return state


class StateTransitions:
    transitions = {
        State.none: [],

        State.pik_today: [State.moscow_today, State.regions_today, State.morton_today, State.pik_yesterday],
        State.pik_yesterday: [State.pik_holidays, State.pik_month],
        State.pik_holidays: [State.pik_month],
        State.pik_month: [],

        State.moscow_today: [State.moscow_yesterday],
        State.moscow_yesterday: [],

        State.regions_today: [State.regions_yesterday],
        State.regions_yesterday: [],

        State.morton_today: [State.morton_month, State.morton_holidays, State.morton_yesterday],
        State.morton_yesterday: [State.morton_holidays, State.morton_month],
        State.morton_holidays: [State.morton_month],
        State.morton_month: []
    }

    @staticmethod
    def get_transition_for_state(state):
        return StateTransitions.transitions[state]
