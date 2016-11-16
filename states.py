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
    sms = "Сводка"


class Type(Enum):
    sold = "sold"
    forecast = "forecast"
    sms = "sms"


class State(Enum):
    none = None, None
    pik_today = (Source.pik, Time.today)
    moscow_today = (Source.moscow, Time.today)
    regions_today = (Source.regions, Time.today)
    pik_yesterday = (Source.pik, Time.yesterday)
    moscow_yesterday = (Source.moscow, Time.yesterday)
    regions_yesterday = (Source.regions, Time.yesterday)

    morton_today = (Source.morton, Time.today)
    morton_yesterday = (Source.morton, Time.yesterday)
    morton_holidays = (Source.morton, Time.holidays)
    morton_month = (Source.morton, Time.month)

    sms_today = (Source.sms, Time.today)
    sms_yesterday = (Source.sms, Time.yesterday)
    sms_holidays = (Source.sms, Time.holidays)
    sms_month = (Source.sms, Time.month)

    def __init__(self, source, time):
        self.source = source
        self.time = time
        self.type = Type.sold

    @property
    def description(self):
        return self.source.value + " " + self.time.value

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
        State.moscow_today: [State.pik_today, State.regions_today, State.morton_today, State.moscow_yesterday],
        State.regions_today: [State.moscow_today, State.pik_today, State.morton_today, State.regions_yesterday],
        State.morton_today: [State.moscow_today, State.regions_today, State.pik_today, State.morton_yesterday],
        State.pik_yesterday: [State.moscow_yesterday, State.regions_yesterday, State.morton_yesterday],
        State.moscow_yesterday: [State.pik_yesterday, State.regions_yesterday, State.morton_yesterday],
        State.regions_yesterday: [State.moscow_yesterday, State.pik_yesterday, State.morton_yesterday],
        State.morton_yesterday: [State.moscow_yesterday, State.regions_yesterday, State.pik_yesterday],
        State.sms_today: [State.sms_yesterday, State.sms_holidays, State.sms_month],
        State.sms_yesterday: [State.sms_holidays, State.sms_month],
        State.sms_holidays: [State.sms_yesterday, State.sms_month],
        State.sms_month: [State.sms_yesterday, State.sms_holidays],
    }

    @staticmethod
    def get_transition_for_state(state):
        return StateTransitions.transitions[state]
