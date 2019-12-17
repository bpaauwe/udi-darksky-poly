#!/usr/bin/env python3
"""
Polyglot v2 node server DarkSky weather data
Copyright (C) 2019 Robert Paauwe
"""

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import sys
import requests
import json
import node_funcs
from nodes import darksky_daily
from nodes import uom

LOGGER = polyinterface.LOGGER

@node_funcs.add_functions_as_methods(node_funcs.functions)
class Controller(polyinterface.Controller):
    id = 'dsweather'
    #id = 'controller'
    hint = [0,0,0,0]
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'DarkSky'
        self.address = 'weather'
        self.primary = self.address
        self.configured = False

        self.params = node_funcs.NSParameters([{
            'name': 'APIKey',
            'default': 'set me',
            'isRequired': True,
            'notice': 'DarkSky API key must be set',
            },
            {
            'name': 'Location',
            'default': '',
            'isRequired': True,
            'notice': 'DarkSky location must be set',
            },
            {
            'name': 'Units',
            'default': 'us',
            'isRequired': False,
            'notice': '',
            },
            {
            'name': 'Forecast Days',
            'default': '0',
            'isRequired': False,
            'notice': '',
            },
            {
            'name': 'Elevation',
            'default': '0',
            'isRequired': False,
            'notice': '',
            },
            {
            'name': 'Plant Type',
            'default': '0.23',
            'isRequired': False,
            'notice': '',
            },
            ])

        self.poly.onConfig(self.process_config)

    # Process changes to customParameters
    def process_config(self, config):
        (valid, changed) = self.params.update_from_polyglot(config)
        if changed and not valid:
            LOGGER.debug('-- configuration not yet valid')
            self.removeNoticesAll()
            self.params.send_notices(self)
        elif changed and valid:
            LOGGER.debug('-- configuration is valid')
            self.removeNoticesAll()
            self.configured = True
            if self.params.isSet('Forecast Days'):
                self.discover()
        elif valid:
            LOGGER.debug('-- configuration not changaed, but is valid')

    def start(self):
        LOGGER.info('Starting node server')
        self.set_logging_level()
        self.check_params()
        self.discover()
        LOGGER.info('Node server started')

        # Do an initial query to get the data filled in as soon as possible
        self.query_conditions(True)

    def shortPoll(self):
        self.query_conditions(False)

    # TODO: Move icon_2_int to a separate file
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

    def get_weather_data(self):
        request = 'https://api.darksky.net/forecast/'
        request += self.params.get('APIKey') + '/'
        request += self.params.get('Location')
        request += '?units=' + self.params.get('Units')

        #TODO: Can we set the number of days of forecast data?

        LOGGER.debug('request = %s' % request)
        try:
            c = requests.get(request)
            jdata = c.json()
            c.close()
            LOGGER.debug(jdata)
        except:
            LOGGER.error('HTTP request failed for api.darksky.net')
            jdata = None

        return jdata


    def query_conditions(self, force=False):
        # Query for the current conditions. We can do this fairly
        # frequently, probably as often as once every 2 minutes.
        #
        # By default JSON is returned

        if not self.configured:
            LOGGER.info('Skipping connection because we aren\'t configured yet.')
            return

        try:
            jdata = self.get_weather_data()

            if jdata == None:
                LOGGER.error('Query returned no data')
                return

            for key in jdata:
                LOGGER.debug('found key: ' + key)
                #LOGGER.debug(jdata[key])

            if 'error' in jdata:
                LOGGER.error('DarkSky reports ' + jdata['error'])
                self.addNotice(jdata['error'], 'error')
                return

            # Assume we always get the main section with data
            # 'currently' is the current conditions
            # 'daily' is the daily forecats

            if 'currently' not in jdata:
                LOGGER.error('No current condition object in query response.')
                # Note that we're also going to skip forecast data now.
                return

            ob = jdata['currently']
            self.update_driver('GV13', self.icon_2_int(ob['icon']), force)
            self.update_driver('CLITEMP', ob['temperature'], force)
            self.update_driver('CLIHUM', float(ob['humidity']) * 100, force)
            self.update_driver('BARPRES', float(ob['pressure']), force)
            self.update_driver('GV4', float(ob['windSpeed']), force)
            self.update_driver('GV5', float(ob['windGust']), force)
            self.update_driver('WINDDIR', float(ob['windBearing']), force)
            self.update_driver('DISTANC', float(ob['visibility']), force)
            self.update_driver('GV14', float(ob['cloudCover'] * 100), force)
            self.update_driver('UV', float(ob['uvIndex']), force, prec=1)
            self.update_driver('GV0', float(ob['apparentTemperature']), force)
            self.update_driver('DEWPT', float(ob['dewPoint']), force)
            self.update_driver('GV10', float(ob['ozone']), force)
            self.update_driver('RAINRT', float(ob['precipIntensity']), force, prec=3)
            self.update_driver('GV18', float(ob['precipProbability']) * 100, force)

            # other possible data
            # nearestStormDistance
            # precipIntensityError
            # precipType

            # Daily data is 7 day forecast, index 0 is today
            num_days = int(self.params.get('Forecast Days'))
            LOGGER.debug('Process forecast data for ' + str(num_days) + ' days')
            for day in range(0,num_days):
                address = 'forecast_' + str(day)
                LOGGER.debug('calling update_forecast for ' + address)
                try:
                    self.nodes[address].update_forecast(jdata['daily']['data'][day], jdata['latitude'], self.params.get('Elevation'), self.params.get('Plant Type'), self.params.get('Units'))
                except:
                    LOGGER.debug('Failed to query forecast data for day ' + day)
        except:
            LOGGER.error('Failed to process data from DarkSky.')
        
    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        # Create forecast nodes here.  We have up to 7 days.
        LOGGER.info("In Discovery...")
        num_days = int(self.params.get('Forecast Days'))

        if num_days < 7:
            for day in range(num_days, 7):
                address = 'forecast_' + str(day)
                try:
                    self.delNode(address)
                except:
                    LOGGER.debug('Failed to delete node ' + address)

        for day in range(0, num_days):
            address = 'forecast_' + str(day)
            title = 'Forecast ' + str(day)
            try:
                node = darksky_daily.DailyNode(self, self.address, address, title)
                self.addNode(node);
            except:
                LOGGER.error('Failed to create forecast node' + title)

        self.set_driver_uom(self.params.get('Units'))

    # Delete the node server from Polyglot
    def delete(self):
        LOGGER.info('Removing node server')

    def stop(self):
        LOGGER.info('Stopping node server')

    def update_profile(self, command):
        st = self.poly.installprofile()
        return st

    def check_params(self):
        self.removeNoticesAll()

        if self.params.get_from_polyglot(self):
            LOGGER.debug('All required parameters are set!')
            self.configured = True
            if int(self.params.get('Forecast Days')) > 7:
                addNotice('Number of days of forecast data is limited to 7 days', 'forecast')
                self.params.set('Forecast Days', 7)
        else:
            LOGGER.debug('Configuration required.')
            LOGGER.debug('APIKey = ' + self.params.get('APIKey'))
            LOGGER.debug('Location = ' + self.params.get('Location'))
            self.params.send_notices(self)

    def set_driver_uom(self, units):
        LOGGER.info('Configure driver units to ' + units)
        self.uom = uom.get_uom(units)
        for day in range(0, int(self.params.get('Forecast Days'))):
            address = 'forecast_' + str(day)
            self.nodes[address].set_driver_uom(units)

    def remove_notices_all(self, command):
        self.removeNoticesAll()

    def set_logging_level(self, level=None):
        if level is None:
            try:
                level = self.get_saved_log_level()
            except:
                LOGGER.error('set_logging_level: get saved log level failed.')

            if level is None:
                level = 30

            level = int(level)
        else:
            level = int(level['value'])

        self.save_log_level(level)
        LOGGER.info('set_logging_level: Setting log level to %d' % level)
        LOGGER.setLevel(level)

    commands = {
            'DISCOVER': discover,
            'UPDATE_PROFILE': update_profile,
            'REMOVE_NOTICES_ALL': remove_notices_all,
            'DEBUG': set_logging_level,
            }

    # For this node server, all of the info is available in the single
    # controller node.
    #
    # TODO: add following status
    #    DISTANC - distance / visibility
    #    SPEED   - speed / wind speed / gust speed
    drivers = [
            {'driver': 'ST', 'value': 1, 'uom': 2},   # node server status
            {'driver': 'CLITEMP', 'value': 0, 'uom': 4},   # temperature
            {'driver': 'GV0', 'value': 0, 'uom': 4},       # apparent temp
            {'driver': 'CLIHUM', 'value': 0, 'uom': 22},   # humidity
            {'driver': 'DEWPT', 'value': 0, 'uom': 4},     # dewpoint
            {'driver': 'BARPRES', 'value': 0, 'uom': 117}, # pressure
            {'driver': 'GV4', 'value': 0, 'uom': 49},      # wind speed
            {'driver': 'WINDDIR', 'value': 0, 'uom': 76},  # direction
            {'driver': 'GV5', 'value': 0, 'uom': 49},      # wind gust
            {'driver': 'GV13', 'value': 0, 'uom': 25},     # climate conditions
            {'driver': 'GV14', 'value': 0, 'uom': 22},     # cloud conditions
            {'driver': 'DISTANC', 'value': 0, 'uom': 116}, # visibility
            {'driver': 'GV18', 'value': 0, 'uom': 22},     # chance
            {'driver': 'RAINRT', 'value': 0, 'uom': 24},   # rain
            {'driver': 'UV', 'value': 0, 'uom': 71},       # UV index
            {'driver': 'GV10', 'value': 0, 'uom': 56},     # Ozone
            ]

