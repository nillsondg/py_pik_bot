from enum import Enum


class Time(Enum):
    today = "Сегодня"
    yesterday = "Вчера"


class Source(Enum):
    pik = "ПИК"
    moscow = "Москва"
    regions = "Регионы"
    morton = "Мортон"


class State(Enum):
    none = None, None
    pik_today = (Source.pik, Time.today)
    moscow_today = (Source.moscow, Time.today)
    regions_today = (Source.regions, Time.today)
    morton_today = (Source.morton, Time.today)
    pik_yesterday = (Source.pik, Time.yesterday)
    moscow_yesterday = (Source.moscow, Time.yesterday)
    regions_yesterday = (Source.regions, Time.yesterday)
    morton_yesterday = (Source.morton, Time.yesterday)

    def __init__(self, source, time):
        self.source = source
        self.time = time

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
    }

    @staticmethod
    def get_transition_for_state(state):
        return StateTransitions.transitions[state]
