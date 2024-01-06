from operator import attrgetter
#from tui import *
from structs import *
from notify_reciver import *
from skyfield.api import load, N, E, S, W, wgs84, Star
from skyfield.data import hipparcos
from skyfield import almanac
import  numpy as np
import csv
import os

class DataGrabber:
    
    notify_reciver: object


    def __init__(self, _notify_reciver: NotifyReciver):
        self.notify_reciver = _notify_reciver


    def getFromFile(self, file_name: str):
        raw_rows = []
        self.notify_reciver('File name provided, trying to open...')
        csv_file = open(file_name, 'r')  
        self.notify_reciver('Getting data from file...')
        i = 0
        for row in csv_file:
            i = i + 1
            row =  row.strip()
            if row and not row.startswith('#'):
                raw_row = row.split('#')
                raw_rows.append(raw_row[0].split(';'))
        self.notify_reciver(str(len(raw_rows)) + '/' +  str(i) + ' lines')
        csv_file.close()
        return raw_rows


class DataChecker:
    
    notify_reciver: object
    solar_system: dict 
    names_file: str
    hipparcos_file_opened = False 
    hipparcos_file_loaded = False
    data: object
    data_frame: object


    def __init__(self, _notify_reciver: NotifyReciver):
        self.notify_reciver = _notify_reciver
        self.names_file = 'the_hipparcos_and_tycho_catalogue_names_file' 
        self.solar_system = dict(zip(['sun', 'earth','moon', 'mars', 'venus',
                                'mercury', 'jupiter', 'saturn',
                                'uran', 'neput', 'pluto'],
                            ['SUN','EARTH','MOON','MARS','VENUS','MERCURY',
                                'JUPITER BARYCENTER','SATURN BARYSENTER',
                                'URAN BARYCENTER','NEPTUN BARYCENTER',
                                'PLUTO BARYCENTER']))
        try:
            self.data = open(self.names_file, 'r')
            self.hipparcos_file_opened = True 
            f = load.open(hipparcos.URL) 
            self.data_frame = hipparcos.load_dataframe(f)
            self.hipparcos_file_loaded = True 
            self.notify_reciver('Opened')
            f.close()
        except: 
            self.notify_reciver('Can not open or download file. Opened: '
                                        + str(self.hipparcos_file_opened)
                                        + '. Loaded: '
                                        + str(self.hipparcos_file_loaded))
   
    def __del__(self):
        if self.hipparcos_file_opened:
            self.data.close()


    def checkPosition(self, _raw_row: tuple[str] ):
        latitude =  _raw_row[0].split(',')
        longitude = _raw_row[1].split(',')
        long_len = len(longitude)
        lat_len = len(latitude)
        if long_len != lat_len:
            raise ValueError('wrong position format')
        if long_len != 2 and long_len != 4:
            raise ValueError('wrong position format')
        if lat_len != 2 and lat_len != 4:
            raise ValueError('wrong position values')
        direction = latitude[lat_len - 1].upper().strip()
        if direction != 'N' and direction != 'S':   
            raise ValueError('wrong position values')
        direction = longitude[long_len - 1].upper().strip()
        if direction != 'E' and direction != 'W':
            raise ValueError('wrong position values')
        if long_len == 2:
            longitude[0] = abs(float(longitude[0]))
            latitude[0] = abs(float(latitude[0]))
            if longitute[0] > 180 or latitude[0] > 90:
                raise ValueError('wrong position values')
            else:
                return Position._make((latitude[0], latitude[1].upper(), longitude[0], longitude[1].upper()))
        else:
            longitude[0] = abs(int(longitude[0]))
            longitude[1] = abs(int(longitude[1]))
            longitude[2] = abs(int(longitude[2]))
            latitude[0] = abs(int(latitude[0]))
            latitude[1] = abs(int(latitude[1]))
            latitude[2] = abs(int(latitude[2]))
            if longitude[1] >= 60 or longitude[2] >= 60 or latitude[1] >= 60 or latitude[2] >=60:
                raise ValueError('wrong position values')
            if longitude[0] == 180 and (longitude[1] != 0 or longitude[2] != 0):
                raise ValueError('wrong position values')
            if latitude[0] == 90 and (latitude[1] != 0 or latitude[2] != 0):
                raise ValueError('wrong position values')
            else:
                return Position._make((latitude[0] + latitude[1] / 60 + latitude[2] / 3600, 
                                latitude[3].upper(),
                                longitude[0] + longitude[1] / 60 + longitude[2] / 3600, 
                                longitude[3].upper())) 


    def checkData(self, _raw_rows):
        bodies = []
        time_scale = load.timescale()
        self.notify_reciver('Loading observations\' data')
        j = 0
        for row in _raw_rows:
            if len(row) != 3 or not row[0] or not row[1] or not row[2]:
                self.notify_reciver('Removing invalid line: ' + str(row))
                continue
            try:
                time = row[1].strip().split('-')
                time2 = row[2].strip().split('-') 
                first_day = time_scale.utc(int(time[2]), 
                                        int(time[1]), 
                                        int(time[0]))
                last_day = time_scale.utc(int(time2[2]), 
                                        int(time2[1]), 
                                        int(time2[0]))
            except: 
                self.notify_reciver('Removing invalid line: ' + str(row))
            else:
                if first_day.utc_datetime() > last_day.utc_datetime():
                    self.notify_reciver('Correccting dates order')
                    first_day, last_day = last_day, first_day
                bodies.append(Body(row[0].strip().capitalize(), [DatesRange(first_day, last_day)]))
                j = j + 1
        self.notify_reciver(str(j) +  ' of ' + str(len(_raw_rows)) + ' entry(ies) accepted')
        i = len(bodies)
        if i == 0:
            return []
        filtered_bodies = [] 
        for body in bodies:
            if body in filtered_bodies:
                print('Merging ', body.name)
                filtered_bodies[filtered_bodies.index(body)].merge(body)
            else:
                filtered_bodies.append(body)
        i = len(filtered_bodies)
        self.notify_reciver(str(i) + ' unique bodies')
        for body in filtered_bodies:
            body.dates_ranges.sort()
            merged_dates = []
            while(len(body.dates_ranges)):
                merged_dates.append(body.dates_ranges.pop(0))
                index = len(merged_dates) - 1
                for date_range in body.dates_ranges.copy():
                    if (date_range.first_day.utc_datetime() 
                            <= (merged_dates[index].last_day + 1).utc_datetime()):
                        if date_range.last_day.utc_datetime() > merged_dates[index].last_day.utc_datetime():
                            merged_dates[index].last_day = date_range.last_day 
                        body.dates_ranges.remove(date_range)
            body.dates_ranges = merged_dates
        return filtered_bodies


    def bodyData(self, _bodies, _eph):
        solar_system_keys = self.solar_system.keys()
        bodies = list() 
        for _body in _bodies:
            self.notify_reciver('Searching for ' + _body.name + '\'s data...')
            self.notify_reciver('in Solar System')
            if _body.name.lower() in solar_system_keys:
                body = Body(_body.name, _body.dates_ranges)
                body.astro_data = _eph[self.solar_system[_body.name.lower()]] 
                bodies.append(body)
                self.notify_reciver('got it')
                continue 

            self.notify_reciver('none')
            if (not self.hipparcos_file_opened 
                    or not self.hipparcos_file_loaded):
                continue
            self.notify_reciver('in Hipparcos and Tycho Catalogue names file')
            self.data.seek(0)
            founded = False
            while True:
                _body_data = self.data.readline()
                if not _body_data:
                    break
                _body_data = _body_data.strip().split(',')
                if not _body.name in _body_data:
                    continue
                self.notify_reciver('Getting data for ' + _body.name + '...')
                body = Body(_body.name, _body.dates_ranges)
                body.astro_data = Star.from_dataframe(self.data_frame.loc[int(len(_body_data) - 1)])
                bodies.append(body)
                self.notify_reciver('got it')
                founded = True
                break
            if not founded:
                self.notify_reciver('none') 
        return bodies



class Calculator:

    notify_reciver: object

    def __init__(self, _notify_reciver):
        self.notify_reciver = _notify_reciver


    def getRisesAndSets(self, _bodies, _eph, place) -> list[Body]:
        bodies = []
        for _body in _bodies:
            self.notify_reciver('Calculating rises and sets for ' + _body.name)
            dates_ranges = []
            body = Body(_body.name, _body.dates_ranges) 
            body.astro_data = _body.astro_data
            for dates_range in _body.dates_ranges: 
                self.notify_reciver('Date range: ' + dates_range.first_day.utc_datetime().strftime('%d-%m-%Y') + ' - ' + dates_range.last_day.utc_datetime().strftime('%d-%m-%Y'))
                _rises_and_sets = almanac.find_discrete(dates_range.first_day,
                                                        dates_range.last_day + 1, 
                                                        almanac.risings_and_settings(_eph, 
                                                                                _body.astro_data,
                                                                                place))
                # we want first rise and set last
                if _rises_and_sets[1][0] == 0:
                    _rises_and_sets = [_rises_and_sets[0][1:],
                                        _rises_and_sets[1][1:]] 
                last_index = len(_rises_and_sets[0]) - 1
                if _rises_and_sets[1][last_index] == 1: 
                    _rises_and_sets =  [_rises_and_sets[0][:last_index], 
                                        _rises_and_sets[1][:last_index]]
                _rise_and_set_pair = np.array(_rises_and_sets[0])
                _rise_and_set_pair = _rise_and_set_pair.reshape(-1, 2)

                i = len(_rise_and_set_pair)
                if i == 0:
                    self.notify_reciver('No rise and set pairs in given dates')
                    continue
                self.notify_reciver(str(i) + ' pairs of rise and set founded')
                _date_range = DatesRange(dates_range.first_day,
                                            dates_range.last_day)
                for _rise_set in _rise_and_set_pair:
                    _date_range.rises_and_sets_pairs.append(RiseAndSetPair(_rise_set[0],
                                                                            _rise_set[1]))
                dates_ranges.append(_date_range) 
            body.dates_ranges = dates_ranges
            self.notify_reciver('--------')
            bodies.append(body)
        return bodies


    def calcRates(self, pos_on_earth, _pos, _bodies):
        time_scale = load.timescale()
        bodies = []
        for _body in _bodies:
            body = Body(_body.name, [])
            self.notify_reciver('Movements for ' + _body.name)
            for dates_range in _body.dates_ranges:
                self.notify_reciver('Date range: ' + dates_range.first_day.utc_datetime().strftime('%d-%m-%Y')
                        + ' - '  + dates_range.last_day.utc_datetime().strftime('%d-%m-%Y'))
                _dates_range = DatesRange(dates_range.first_day, dates_range.last_day)
                for rise_and_set_pair in dates_range.rises_and_sets_pairs:
                    time_of_rise = rise_and_set_pair.time_of_rise
                    time_of_set = rise_and_set_pair.time_of_set
                    self.notify_reciver('Seconds between '
                                    + time_of_rise.utc_datetime().strftime('%d-%m-%Y %H:%M:%S')
                                    + ' and '
                                    + time_of_set.utc_datetime().strftime('%d-%m-%Y %H:%M:%S')
                                    +  '... ')
                    delta_in_seconds = (time_of_set.utc_datetime()
                                        - time_of_rise.utc_datetime()) // datetime.timedelta(seconds = 1)
                    seconds = time_scale.utc(time_of_rise.utc_datetime().year, 
                                            time_of_rise.utc_datetime().month, 
                                            time_of_rise.utc_datetime().day, 
                                            time_of_rise.utc_datetime().hour, 
                                            time_of_rise.utc_datetime().minute, 
                                            range(time_of_rise.utc_datetime().second, delta_in_seconds))
                    self.notify_reciver(delta_in_seconds)
    
                    self.notify_reciver.setLiveData('Calculating movement\'s rates', delta_in_seconds)
                    seconds_rates = []
                    i = 0
                    for spec_time in seconds:
                        a = pos_on_earth.at(spec_time).observe(_body.astro_data).apparent()
                        alt, az, distance, alt_rate, az_rate, range_rate = a.frame_latlon_and_rates(_pos)
                        _, _, _, alt_rate, az_rate, _ = a.frame_latlon_and_rates(_pos)
                        seconds_rates.append(MovementsRates(spec_time.utc_datetime().strftime('%H:%M:%S'),
                                                round(alt_rate.degrees.per_second, 4),
                                                round(az_rate.degrees.per_second, 4)))
                        i += 1
                        self.notify_reciver.updateLiveData(i)
                    self.notify_reciver.finishLiveData()
                    
                    self.notify_reciver('Removing redundant data...\n') 
                    actual_alt = seconds_rates[0].alt_rate
                    actual_az = seconds_rates[0].az_rate
                    for second_rate in seconds_rates[1:].copy():
                        if (actual_alt == second_rate.alt_rate
                                and actual_az == second_rate.az_rate):
                            seconds_rates.remove(second_rate) 
                        else:
                            actual_alt = second_rate.alt_rate
                            actual_az = second_rate.az_rate
                    _rise_and_set_pair = RiseAndSetPair(time_of_rise, time_of_set)
                    _rise_and_set_pair.movements =  seconds_rates
                    _dates_range.rises_and_sets_pairs.append(_rise_and_set_pair)
                body.dates_ranges.append(_dates_range)
            self.notify_reciver('--------')
            bodies.append(body)
        return bodies 



class DataSaver:

    notify_reciver: object

    def __init__(self, notify_reciver: NotifyReciver):
        self.notify_reciver = notify_reciver
        try:
            os.mkdir('calculations')
        except OSError:
            self.notify_reciver('Destination dir exists')
        else:
            self.notify_reciver('Creating destination dir')


    def saveCSV(self, _bodies: [Body]):
        for body in _bodies:
            for date_range in body.dates_ranges:
                file_name = 'calculations/' + (body.name
                    + '_'
                    + date_range.first_day.utc_datetime().strftime('%d-%m-%Y')
                    + '_'
                    + date_range.last_day.utc_datetime().strftime('%d-%m-%Y')
                    + '.csv')
                with open(file_name, 'w') as file:
                    writer = csv.writer(file)
                    for rise_and_set_pair in date_range.rises_and_sets_pairs: 
                        row = ['Rise',
                                rise_and_set_pair.time_of_rise.utc_datetime().strftime('%d-%m-%Y %H:%M:%S'),
                                'Set',
                                rise_and_set_pair.time_of_set.utc_datetime().strftime('%d-%m-%Y %H:%M:%S')] 
                        writer.writerow(row)
                        for movement in rise_and_set_pair.movements:
                            row = [movement.time, movement.alt_rate, movement.az_rate]
                            writer.writerow(row)
