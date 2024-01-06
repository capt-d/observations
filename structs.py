from collections import namedtuple
from dataclasses import dataclass, field
import datetime

Position = namedtuple('Position', ['latitude', 'NS', 'longitude', 'WE'])#, 
                        #defaults = [0, 'N', 0, 'E'])
MovementsRates = namedtuple('MovementsRates', ['time', 'alt_rate', 'az_rate'])#,
                            #defaults=[datetime.time(), 0, 0])

@dataclass(init = False)
class RiseAndSetPair:
    time_of_rise: datetime
    time_of_set: datetime
    movements: list[MovementsRates] 

    def __init__(self, _rise: datetime, _set:datetime):
        self.time_of_rise = _rise
        self.time_of_set = _set
        self.movements = [] 

            
@dataclass(init = False)
class DatesRange:
    first_day: datetime
    last_day: datetime
    rises_and_sets_pairs: list[RiseAndSetPair] 

    def __init__(self, fd: datetime, ld: datetime):
        self.first_day = fd
        self.last_day = ld
        self.rises_and_sets_pairs = []  

    def __gt__(self, _other):
        return (_other.first_day.utc_datetime() < self.first_day.utc_datetime())

    def __ne__(self, _other):
        return (_other.first_day.utc_datetime() != self.first_day.utc_datetime() 
                or _other.last_day.utc_datetime() != self.last_day.utc_datetime())

    def __eq__(self, _other):
        return (_other.first_day.utc_datetime() == self.first_day.utc_datetime() 
                and _other.last_day.utc_datetime() == self.last_day.utc_datetime())


@dataclass(init = False)
class Body:
    name: str
    astro_data: object #= field(init = False)
    dates_ranges: list[DatesRange] 

    def __init__(self, name, dates_ranges: list[DatesRange]):
        self.name = name
        self.astro_data = '' 
        self.dates_ranges = dates_ranges 
   
    def __eq__(self, other):
        return (self.name) == (other.name)
    
    def merge(self, _body):
        for _date_range in _body.dates_ranges:
            if _date_range not in self.dates_ranges:
                self.dates_ranges.append(_date_range)
         
  
@dataclass(init = False)
class CalculationsResults:
    """ All callculations result are keeped here """
    earth: object #= field(init = False)
    pos_on_earth: object #= field(init = False)
    position: Position #= field(init = False)
    bodies: list[Body] #= field(init = False)   # [Body.name, Body.astro_data] 

    def __init__(self):
        self.bodies = []


