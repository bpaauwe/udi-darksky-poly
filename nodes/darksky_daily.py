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
            {'driver': 'CLIHUM', 'value': 0, 'uom': 22},   # humidity
            {'driver': 'DEWPT', 'value': 0, 'uom': 4},     # dewpoint       *
            {'driver': 'BARPRES', 'value': 0, 'uom': 117}, # pressure
            {'driver': 'GV13', 'value': 0, 'uom': 25},     # conditions
            {'driver': 'GV14', 'value': 0, 'uom': 22},     # clouds
            {'driver': 'GV4', 'value': 0, 'uom': 49},      # wind speed     *
            {'driver': 'GV5', 'value': 0, 'uom': 49},      # gust speed     *
            {'driver': 'WINDDIR', 'value': 0, 'uom': 76},  # wind dir       *
            {'driver': 'GV7', 'value': 0, 'uom': 82},      # precipitation  *
            {'driver': 'GV18', 'value': 0, 'uom': 22},     # precip chance
            {'driver': 'UV', 'value': 0, 'uom': 71},       # UV index
            {'driver': 'GV10', 'value': 0, 'uom': 56},     # ozone          *
            {'driver': 'DISTANC', 'value': 0, 'uom': 83},  # visibility     *
            {'driver': 'GV9', 'value': 0, 'uom': 56},      # moon phase     *
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

    def update_forecast(self, jdata, latitude, elevation, plant_type, units, force):
        epoch = int(jdata['time'])
        dow = time.strftime("%w", time.gmtime(epoch))
        LOGGER.info('Day of week = ' + dow)
        try:
            self.update_driver('CLIHUM', round(float(jdata['humidity']) * 100, 0), force)
            self.update_driver('BARPRES', jdata['pressure'], force)
            self.update_driver('GV0', jdata['temperatureMax'], force)
            self.update_driver('GV1', jdata['temperatureMin'], force)
            self.update_driver('GV13', self.icon_2_int(jdata['icon']), force)
            self.update_driver('GV14', round(float(jdata['cloudCover']) * 100, 0), force)
            self.update_driver('UV', jdata['uvIndex'], force)
            self.update_driver('GV18', float(jdata['precipProbability']) * 100, force)
            self.update_driver('GV19', int(dow), force)
            self.update_driver('DEWPT', jdata['dewPoint'], force)
            self.update_driver('GV4', jdata['windSpeed'], force)
            self.update_driver('GV5', jdata['windGust'], force)
            self.update_driver('WINDDIR', jdata['windBearing'], force)
            if 'precipAccumulation' in jdata:
                self.update_driver('GV7', jdata['precipAccumulation'], force)
            else:
                self.update_driver('GV7', 0, force)
            self.update_driver('GV10', jdata['ozone'], force)
            self.update_driver('DISTANC', jdata['visibility'], force)
            self.update_driver('GV9', jdata['moonPhase'], force)
        except Exception as e:
            LOGGER.error('Update failed: ' + str(e))

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
        if self.units == 'metric' or self.units == 'si' or self.units.startswith('m'):
            self.update_driver('GV20', round(et0, 2), force)
        else:
            self.update_driver('GV20', round(self.mm2inch(et0), 3), force)
        LOGGER.info("ETo = %f %f" % (et0, self.mm2inch(et0)))


