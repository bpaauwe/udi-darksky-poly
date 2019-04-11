#!/usr/bin/env python3
"""
Polyglot v2 node server DarkSky weather data
Copyright (C) 2019 Robert Paauwe
"""

CLOUD = False
try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True
import sys
import requests
import json
import darksky_daily
import write_profile

LOGGER = polyinterface.LOGGER

class Controller(polyinterface.Controller):
    id = 'dsweather'
    #id = 'controller'
    hint = [0,0,0,0]
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'DarkSky'
        self.address = 'weather'
        self.primary = self.address
        self.location = ''
        self.apikey = ''
        self.units = 'us'
        self.configured = False
        self.myConfig = {}

        self.poly.onConfig(self.process_config)

    # Process changes to customParameters
    def process_config(self, config):
        if 'customParams' in config:
            # Check if anything we care about was changed...
            if config['customParams'] != self.myConfig:
                changed = False
                if 'Location' in config['customParams']:
                    if self.location != config['customParams']['Location']:
                        self.location = config['customParams']['Location']
                        changed = True
                if 'APIkey' in config['customParams']:
                    if self.apikey != config['customParams']['APIkey']:
                        self.apikey = config['customParams']['APIkey']
                        changed = True
                if 'Units' in config['customParams']:
                    if self.units != config['customParams']['Units']:
                        self.units = config['customParams']['Units']
                        changed = True
                        if CLOUD:
                            self.set_cloud_driver_units()
                        else:
                            self.set_driver_units()

                self.myConfig = config['customParams']
                if changed:
                    self.removeNoticesAll()
                    self.configured = True

                    if self.location == '':
                        self.addNotice("Location parameter must be set");
                        self.configured = False
                    if self.apikey == '':
                        self.addNotice("OpenWeatherMap API ID must be set");
                        self.configured = False

    def start(self):
        LOGGER.info('Starting node server')
        LOGGER.info('Add node for forecast')
        for day in range(1,8):
            address = 'forecast_' + str(day)
            title = 'Forcast ' + str(day)

            try:
                node = darksky_daily.DailyNode(self, self.address, address, title)
                self.addNode(node);
            except:
                LOGGER.error('Failed to create forecast node' + title)

        self.check_params()
        LOGGER.info('Node server started')

        # Do an initial query to get the data filled in as soon as possible
        self.query_conditions()

    def shortPoll(self):
        self.query_conditions()

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

    def query_conditions(self):
        # Query for the current conditions. We can do this fairly
        # frequently, probably as often as once every 2 minutes.
        #
        # By default JSON is returned

        request = 'https://api.darksky.net/forecast/'
        # TODO: handle other methods of setting location
        request += self.apikey + '/'
        request += self.location

        # units= 'auto' 'ca' 'si' 'us' 'uk2'
        request += '?units=' + self.units

        LOGGER.debug('request = %s' % request)

        if not self.configured:
            LOGGER.info('Skipping connection because we aren\'t configured yet.')
            return

        c = requests.get(request)
        jdata = c.json()
        #LOGGER.debug(jdata)
        #LOGGER.debug(jdata['currently'])

        for key in jdata:
            LOGGER.debug('found key: ' + key)
            #LOGGER.debug(jdata[key])

        # Assume we always get the main section with data
        # TODO: Convert icon to number that maps to condition string
        #       in NLS
        #  values: 'clear-day' 'clear-night' 'rain' 'snow' 'sleet' 'wind'
        #          'fog' 'cloudy' 'partly-cloudy-day' 'partly cloudy-night'
        self.setDriver('GV13', self.icon_2_int(jdata['currently']['icon']),
                report=True, force=True)
        self.setDriver('CLITEMP', float(jdata['currently']['temperature']),
                report=True, force=True)
        self.setDriver('CLIHUM', float(jdata['currently']['humidity']) * 100,
                report=True, force=True)
        self.setDriver('BARPRES', float(jdata['currently']['pressure']),
                report=True, force=True)
        self.setDriver('GV4', float(jdata['currently']['windSpeed']),
                report=True, force=True)
        self.setDriver('GV5', float(jdata['currently']['windGust']),
                report=True, force=True)
        self.setDriver('WINDDIR', float(jdata['currently']['windBearing']),
                report=True, force=True)
        self.setDriver('GV15', float(jdata['currently']['visibility']),
                report=True, force=True)
        self.setDriver('GV14', float(jdata['currently']['cloudCover'] * 100),
                report=True, force=True)
        self.setDriver('GV16', float(jdata['currently']['uvIndex']), True, True)
        self.setDriver('GV0', float(jdata['currently']['apparentTemperature']),
                report=True, force=True)
        self.setDriver('DEWPT', float(jdata['currently']['dewPoint']),
                report=True, force=True)
        self.setDriver('GV6', float(jdata['currently']['precipIntensity']),
                report=True, force=True)
        self.setDriver('GV17', float(jdata['currently']['ozone']), True, True)

        # other data
        # nearestStormDistance
        # precipIntensityError
        # precipProbability
        # precipType

        # Daily data is 7 day forecast, index 0 is today
        for day in range(1,8):
            address = 'forecast_' + str(day)
            self.nodes[address].update_forecast(jdata['daily']['data'][day], jdata['latitude'])
        
    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        # Create any additional nodes here
        LOGGER.info("In Discovery...")

    # Delete the node server from Polyglot
    def delete(self):
        LOGGER.info('Removing node server')

    def stop(self):
        LOGGER.info('Stopping node server')

    def update_profile(self, command):
        st = self.poly.installprofile()
        return st

    def check_params(self):

        if 'Location' in self.polyConfig['customParams']:
            self.location = self.polyConfig['customParams']['Location']
        if 'APIkey' in self.polyConfig['customParams']:
            self.apikey = self.polyConfig['customParams']['APIkey']
        if 'Units' in self.polyConfig['customParams']:
            self.units = self.polyConfig['customParams']['Units']
        else:
            self.units = 'us';

        self.configured = True

        self.addCustomParam( {
            'Location': self.location,
            'APIkey': self.apikey,
            'Units': self.units } )

        LOGGER.info('api id = %s' % self.apikey)

        self.removeNoticesAll()
        if self.location == '':
            self.addNotice("Location parameter must be set");
            self.configured = False
        if self.apikey == '':
            self.addNotice("DarkSky API ID must be set");
            self.configured = False

        if CLOUD:
            self.set_cloud_driver_units()
        else:
            self.set_driver_units()

    def set_cloud_driver_units(self):
        LOGGER.info('Configure driver units to ' + self.units)
        if self.units == 'si':
            for drv in self.drivers:
                if drv == 'CLITEMP': self.drivers[drv]['uom'] = 4
                if drv == 'DEWPT': self.drivers[drv]['uom'] = 4
                if drv == 'GV0': self.drivers[drv]['uom'] = 4
                if drv == 'GV1': self.drivers[drv]['uom'] = 4
                if drv == 'GV2': self.drivers[drv]['uom'] = 4
                if drv == 'GV3': self.drivers[drv]['uom'] = 4
                if drv == 'BARPRES': self.drivers[drv]['uom'] = 118
                if drv == 'GV4': self.drivers[drv]['uom'] = 49
                if drv == 'GV5': self.drivers[drv]['uom'] = 49
                if drv == 'RAINRT': self.drivers[drv]['uom'] = 46
                if drv == 'GV15': self.drivers[drv]['uom'] = 38
            for day in range(1,8):
                address = 'forecast_' + str(day)
                self.nodes[address].set_units('si')
        else:
            for drv in self.drivers:
                if drv == 'CLITEMP': self.drivers[drv]['uom'] = 17
                if drv == 'DEWPT': self.drivers[drv]['uom'] = 17
                if drv == 'GV0': self.drivers[drv]['uom'] = 17
                if drv == 'GV1': self.drivers[drv]['uom'] = 17
                if drv == 'GV2': self.drivers[drv]['uom'] = 17
                if drv == 'GV3': self.drivers[drv]['uom'] = 17
                if drv == 'BARPRES': self.drivers[drv]['uom'] = 117
                if drv == 'GV4': self.drivers[drv]['uom'] = 48
                if drv == 'GV5': self.drivers[drv]['uom'] = 48
                if drv == 'RAINRT': self.drivers[drv]['uom'] = 24
                if drv == 'GV15': self.drivers[drv]['uom'] = 116
            for day in range(1,8):
                address = 'forecast_' + str(day)
                self.nodes[address].set_units('us')

    def set_driver_units(self):
        LOGGER.info('Configure drivers ---')
        if self.units == 'si':
            for driver in self.drivers:
                if driver['driver'] == 'CLITEMP': driver['uom'] = 4
                if driver['driver'] == 'DEWPT': driver['uom'] = 4
                if driver['driver'] == 'BARPRES': driver['uom'] = 118
                if driver['driver'] == 'GV0': driver['uom'] = 4
                if driver['driver'] == 'GV1': driver['uom'] = 4
                if driver['driver'] == 'GV2': driver['uom'] = 4
                if driver['driver'] == 'GV3': driver['uom'] = 4
                if driver['driver'] == 'GV4': driver['uom'] = 49
                if driver['driver'] == 'GV5': driver['uom'] = 49
                if driver['driver'] == 'RAINRT': driver['uom'] = 46
                if driver['driver'] == 'GV15': driver['uom'] = 38
            for day in range(1,8):
                address = 'forecast_' + str(day)
                self.nodes[address].set_units('si')

        # Write out a new node definition file here.
        else:  # imperial
            for driver in self.drivers:
                if driver['driver'] == 'CLITEMP': driver['uom'] = 17
                if driver['driver'] == 'DEWPT': driver['uom'] = 17
                if driver['driver'] == 'BARPRES': driver['uom'] = 117
                if driver['driver'] == 'GV0': driver['uom'] = 17
                if driver['driver'] == 'GV1': driver['uom'] = 17
                if driver['driver'] == 'GV2': driver['uom'] = 17
                if driver['driver'] == 'GV3': driver['uom'] = 17
                if driver['driver'] == 'GV4': driver['uom'] = 48
                if driver['driver'] == 'GV5': driver['uom'] = 48
                if driver['driver'] == 'RAINRT': driver['uom'] = 24
                if driver['driver'] == 'GV15': driver['uom'] = 116
            for day in range(1,8):
                address = 'forecast_' + str(day)
                self.nodes[address].set_units('us')

        # Write out a new node definition file here.
        LOGGER.info('Write new node definitions and publish to ISY')
        write_profile.write_profile(LOGGER, self.drivers, self.nodes['forecast_1'].drivers)
        self.poly.installprofile()

    def remove_notices_all(self, command):
        self.removeNoticesAll()


    commands = {
            'DISCOVER': discover,
            'UPDATE_PROFILE': update_profile,
            'REMOVE_NOTICES_ALL': remove_notices_all
            }

    # For this node server, all of the info is available in the single
    # controller node.
    #
    # TODO: Do we want to try and do evapotranspiration calculations? 
    #       maybe later as an enhancement.
    # TODO: Add forecast data
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
            {'driver': 'GV15', 'value': 0, 'uom': 116},    # visibility
            {'driver': 'GV18', 'value': 0, 'uom': 22},     # chance
            {'driver': 'RAINRT', 'value': 0, 'uom': 24},   # rain
            {'driver': 'GV16', 'value': 0, 'uom': 71},     # UV index
            {'driver': 'GV17', 'value': 0, 'uom': 56},     # Ozone
            ]


    
if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('DARKSKY')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        

