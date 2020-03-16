# Node definition for a daily forecast node

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import json
import time
import datetime
from nodes import et3
from nodes import uom
import node_funcs

LOGGER = polyinterface.LOGGER

@node_funcs.add_functions_as_methods(node_funcs.functions)
class DailyNode(polyinterface.Node):
    id = 'daily'
    drivers = [
            {'driver': 'GV19', 'value': 0, 'uom': 25},     # day of week
            {'driver': 'GV0', 'value': 0, 'uom': 4},       # high temp
            {'driver': 'GV1', 'value': 0, 'uom': 4},       # low temp
            {'driver': 'GV18', 'value': 0, 'uom': 22},     # precip chance
            {'driver': 'CLIHUM', 'value': 0, 'uom': 22},   # humidity
            {'driver': 'BARPRES', 'value': 0, 'uom': 117}, # pressure
            {'driver': 'GV13', 'value': 0, 'uom': 25},     # conditions
            {'driver': 'GV14', 'value': 0, 'uom': 22},     # clouds
            {'driver': 'UV', 'value': 0, 'uom': 71},       # UV index
            {'driver': 'GV20', 'value': 0, 'uom': 106},    # mm/day
            ]

    def set_driver_uom(self, units):
        self.uom = uom.get_uom(units)
        self.units = units

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
        self.update_driver('CLIHUM', round(float(jdata['humidity']) * 100, 0))
        self.update_driver('BARPRES', float(jdata['pressure']))
        self.update_driver('GV0', float(jdata['temperatureMax']))
        self.update_driver('GV1', float(jdata['temperatureMin']))
        self.update_driver('GV13', self.icon_2_int(jdata['icon']))
        self.update_driver('GV14', round(float(jdata['cloudCover']) * 100, 0))
        self.update_driver('UV', float(jdata['uvIndex']))
        self.update_driver('GV18', float(jdata['precipProbability']) * 100)
        self.update_driver('GV19', int(dow))

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
        self.update_driver('GV20', round(et0, 2))
        LOGGER.info("ETo = %f %f" % (et0, self.mm2inch(et0)))


