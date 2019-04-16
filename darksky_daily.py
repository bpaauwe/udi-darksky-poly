# Node definition for a daily forecast node

CLOUD = False
try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True

import json
import time
import datetime
import et3

LOGGER = polyinterface.LOGGER

class DailyNode(polyinterface.Node):
    id = 'daily'
    drivers = [
            {'driver': 'GV19', 'value': 0, 'uom': 25},     # day of week
            {'driver': 'GV1', 'value': 0, 'uom': 4},       # high temp
            {'driver': 'GV2', 'value': 0, 'uom': 4},       # low temp
            {'driver': 'GV18', 'value': 0, 'uom': 22},     # precip chance
            {'driver': 'CLIHUM', 'value': 0, 'uom': 22},   # humidity
            {'driver': 'BARPRES', 'value': 0, 'uom': 117}, # pressure
            {'driver': 'GV13', 'value': 0, 'uom': 25},     # conditions
            {'driver': 'GV14', 'value': 0, 'uom': 22},     # clouds
            {'driver': 'GV16', 'value': 0, 'uom': 71},     # UV index
            {'driver': 'GV20', 'value': 0, 'uom': 106},    # mm/day
            ]

    def set_units(self, units):
        try:
            for driver in self.drivers:
                if units == 'us':
                    if driver['driver'] == 'BARPRES': driver['uom'] = 117
                    if driver['driver'] == 'GV1': driver['uom'] = 17
                    if driver['driver'] == 'GV2': driver['uom'] = 17
                    if driver['driver'] == 'GV19': driver['uom'] = 25
                elif units == 'si':
                    if driver['driver'] == 'BARPRES': driver['uom'] = 118
                    if driver['driver'] == 'GV1': driver['uom'] = 4
                    if driver['driver'] == 'GV2': driver['uom'] = 4
                    if driver['driver'] == 'GV19': driver['uom'] = 25
        except:
            for drv in self.drivers:
                if units == 'us':
                    if drv == 'BARPRES': self.drivers[drv]['uom'] = 117
                    if drv == 'GV1': self.drivers[drv]['uom'] = 17
                    if drv == 'GV2': self.drivers[drv]['uom'] = 17
                    if drv == 'GV19': self.drivers[drv]['uom'] = 25
                elif units == 'si':
                    if drv == 'BARPRES': self.drivers[drv]['uom'] = 118
                    if drv == 'GV1': self.drivers[drv]['uom'] = 4
                    if drv == 'GV2': self.drivers[drv]['uom'] = 4
                    if drv == 'GV19': self.drivers[drv]['uom'] = 25

    def icon_2_int(self, icn):
        return {
                'clear-day': 0,
                'clear-night': 1,
                'rain': 2,
                'snow': 3,
                'sleet': 4,
                'wind': 5,
                'fog': 6,
                'cloudy': 7,
                'partly-cloudy-day': 8,
                'partly-cloudy-night': 9,
                }.get(icn, 0)

    def mm2inch(self, mm):
        return mm/25.4

    def update_forecast(self, jdata, latitude, elevation, plant_type, units):
        epoch = int(jdata['time'])
        dow = time.strftime("%w", time.gmtime(epoch))
        LOGGER.info('Day of week = ' + dow)
        self.setDriver('CLIHUM', round(float(jdata['humidity']) * 100, 0), True, False)
        self.setDriver('BARPRES', float(jdata['pressure']), True, False)
        self.setDriver('GV1', float(jdata['temperatureMax']), True, False)
        self.setDriver('GV2', float(jdata['temperatureMin']), True, False)
        self.setDriver('GV13', self.icon_2_int(jdata['icon']), True, False)
        self.setDriver('GV14', round(float(jdata['cloudCover']) * 100, 0), True, False)
        self.setDriver('GV16', float(jdata['uvIndex']), True, False)
        self.setDriver('GV18', float(jdata['precipProbability']) * 100, True, False)
        self.setDriver('GV19', int(dow), True, False)

        # Calculate ETo
        #  Temp is in degree C and windspeed is in m/s, we may need to
        #  convert these.
        Tmin = float(jdata['temperatureMin'])
        Tmax = float(jdata['temperatureMax'])
        Hmin = Hmax = float(jdata['humidity'])
        Ws = float(jdata['windSpeed'])
        J = datetime.datetime.fromtimestamp(jdata['time']).timetuple().tm_yday

        if units != 'si':
            LOGGER.info('Conversion of temperature/wind speed required')
            Tmin = et3.FtoC(Tmin)
            Tmax = et3.FtoC(Tmax)
            Ws = et3.mph2ms(Ws)

        et0 = et3.evapotranspriation(Tmax, Tmin, None, Ws, float(elevation), Hmax, Hmin, latitude, float(plant_type), J)
        self.setDriver('GV20', round(et0, 2), True, False)
        LOGGER.info("ETo = %f %f" % (et0, self.mm2inch(et0)))


