from enum import Enum


class Time(Enum):
    none = 0
    today = 1
    yesterday = 2


class Source(Enum):
    none = 0
    pik = 1
    moscow = 2
    regions = 3
    morton = 4


class Filter:
    time = Time.none
    source = Source.none

    def set_time(self, time):
        self.time = time

    def set_source(self, source):
        self.source = source

    def clear(self):
        self.time = Time.none
        self.source = Source.none

    def is_clear(self):
        return self.time == Time.none or self.source == Source.none
