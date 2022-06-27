import math

class Event:

    def __init__(self, rank_id, function, start_time, end_time, level, tid, args):
        self.rank_id = rank_id
        self.function = function
        self.start_time = start_time
        self.end_time = end_time
        self.level = level
        self.tid = tid
        self.args = args

    def get_start_time_ticks(self, timer_resolution):
        return math.ceil(self.start_time*timer_resolution)

    def get_end_time_ticks(self, timer_resolution):
        return math.ceil(self.end_time*timer_resolution)

