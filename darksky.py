#!/usr/bin/env python3
"""
Polyglot v2 node server DarkSky weather data
Copyright (C) 2019 Robert Paauwe
"""
import polyinterface
import sys
import time
import datetime
import urllib3
import socket
import math
import json
import write_profile

LOGGER = polyinterface.LOGGER

class Controller(polyinterface.Controller):
    id = 'weather'
    #id = 'controller'
    hint = [0,0,0,0]
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'DarkSkey'
        self.address = 'weather'
        self.primary = self.address
        self.location = ''
        self.apikey = ''
        self.units = 'metric'
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
        self.check_params()
        # TODO: Discovery
        LOGGER.info('Node server started')

    def longPoll(self):
        self.query_forecast()

    def shortPoll(self):
        self.query_conditions()

    def query_conditions(self):
        # Query for the current conditions. We can do this fairly
        # frequently, probably as often as once every 2 minutes.
        #
        # By default JSON is returned

        request = 'https://api.darksky.net/forecast/'
        # TODO: handle other methods of setting location
        request += '&appid=' + self.apikey + '/'
        request += 'location=' + self.location

        # units= 'auto' 'ca' 'si' 'us' 'uk2'
        #request += '?units=' + self.units

        LOGGER.debug('request = %s' % request)

        if not self.configured:
            LOGGER.info('Skipping connection because we aren\'t configured yet.')
            return

        http = urllib3.PoolManager()
        c = http.request('GET', request)
        wdata = c.data
        jdata = json.loads(wdata.decode('utf-8'))
        c.close()

        http.clear()

        LOGGER.debug(jdata)

        # Assume we always get the main section with data
        # TODO: Convert icon to number that maps to condition string
        #       in NLS
        #  values: 'clear-day' 'clear-night' 'rain' 'snow' 'sleet' 'wind'
        #          'fog' 'cloudy' 'partly-cloudy-day' 'partly cloudy-night'
        #self.setDriver('GV13', jdata['currently']['icon'],
        #        report=True, force=True)

        self.setDriver('CLITEMP', float(jdata['currently']['temperature']),
                report=True, force=True)
        self.setDriver('CLIHUM', float(jdata['currently']['humidity']),
                report=True, force=True)
        self.setDriver('BARPRES', float(jdata['currently']['pressure']),
                report=True, force=True)
        self.setDriver('GV4', float(jdata['currently']['windSpeed']),
                report=True, force=True)
        self.setDriver('WINDDIR', float(jdata['currently']['windBearing']),
                report=True, force=True)
        self.setDriver('GV15', float(jdata['currently']['visibility']),
                report=True, force=True)
        self.setDriver('GV14', float(jdata['currently']['cloudCover']),
                report=True, force=True)
        self.setDriver('GV16', float(jdata['currently']['uvIndex']), True, True)
        self.setDriver('GV0', float(jdata['currently']['apparentTemperature']),
                report=True, force=True)
        self.setDriver('DEWPT', float(jdata['currently']['dewPoint']),
                report=True, force=True)

        # other data
        # nearestStormDistance
        # precipIntensity
        # precipIntensityError
        # precipProbability
        # precipType
        # windGust
        # ozone
        
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
            self.units = 'metric';

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

        self.set_driver_units()

    def set_driver_units(self):
        LOGGER.info('Configure drivers ---')
        if self.units == 'metric':
            for driver in self.drivers:
                if driver['driver'] == 'CLITEMP':
                    driver['uom'] = 4
                if driver['driver'] == 'DEWPT':
                    driver['uom'] = 4
                if driver['driver'] == 'GV0':
                    driver['uom'] = 4
                if driver['driver'] == 'GV1':
                    driver['uom'] = 4
                if driver['driver'] == 'GV2':
                    driver['uom'] = 4
                if driver['driver'] == 'GV3':
                    driver['uom'] = 4
                if driver['driver'] == 'GV4':
                    driver['uom'] = 49
                if driver['driver'] == 'GV5':
                    driver['uom'] = 49
        else:  # imperial
            for driver in self.drivers:
                if driver['driver'] == 'CLITEMP':
                    driver['uom'] = 17
                if driver['driver'] == 'DEWPT':
                    driver['uom'] = 17
                if driver['driver'] == 'GV0':
                    driver['uom'] = 17
                if driver['driver'] == 'GV1':
                    driver['uom'] = 17
                if driver['driver'] == 'GV2':
                    driver['uom'] = 17
                if driver['driver'] == 'GV3':
                    driver['uom'] = 17
                if driver['driver'] == 'GV4':
                    driver['uom'] = 48
                if driver['driver'] == 'GV5':
                    driver['uom'] = 48

        # Write out a new node definition file here.
        write_profile.write_profile(LOGGER, self.drivers)
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
            {'driver': 'CLIHUM', 'value': 0, 'uom': 22},   # humidity
            {'driver': 'BARPRES', 'value': 0, 'uom': 118}, # pressure
            {'driver': 'WINDDIR', 'value': 0, 'uom': 76},  # direction
            {'driver': 'DEWPT', 'value': 0, 'uom': 4},     # dewpoint
            {'driver': 'GV0', 'value': 0, 'uom': 4},       # apparent temp
            {'driver': 'GV1', 'value': 0, 'uom': 4},       # min temp
            {'driver': 'GV4', 'value': 0, 'uom': 49},      # wind speed
            {'driver': 'GV6', 'value': 0, 'uom': 82},      # rain
            {'driver': 'GV11', 'value': 0, 'uom': 27},     # climate coverage
            {'driver': 'GV12', 'value': 0, 'uom': 70},     # climate intensity
            {'driver': 'GV13', 'value': 0, 'uom': 25},     # climate conditions
            {'driver': 'GV14', 'value': 0, 'uom': 22},     # cloud conditions
            {'driver': 'GV15', 'value': 0, 'uom': 38},     # visibility
            {'driver': 'GV16', 'value': 0, 'uom': 71},     # UV index
            ]


    
if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('DARKSKY')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        

