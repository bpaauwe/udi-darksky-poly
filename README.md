
# DarkSky node server

This is the DarkSky node server for the [Universal Devices ISY994i](https://www.universal-devices.com/residential/ISY) [Polyglot interface](http://www.universal-devices.com/developers/polyglot/docs/) with  [Polyglot V2](https://github.com/Einstein42/udi-polyglotv2)
(c) 2018 Robert Paauwe
MIT license.

This node server is intended to pull weather related data from [DarkSky](http://www.darksky.net/) and make it available via ISY nodes. To access this data you must register with darksky.net and obtain an API key. Note that currently the first 1000 requests per day are free. This means setting the polling to something more frequently than 2 minutes will incur usage charges.

## Installation

1. Backup Your ISY in case of problems!
   * Really, do the backup, please
2. Go to the Polyglot Store in the UI and install.
3. Add NodeServer in Polyglot Web
   * After the install completes, Polyglot will reboot your ISY, you can watch the status in the main polyglot log.
4. Once your ISY is back up open the Admin Console.
5. Configure the node server with the following custom parameters:
- APIkey   : Your API ID, needed to authorize connection to the DarkSky API.

- Location : latitude and longitude of the location to query the data for. ex: 42.3601,-71.0589

- Forecast Days : The number of days of forecast data to track.

- Units    : 'si' or 'us' request data in this units format.

- Elevation : The elevation, in meters, of the location.

- Plant Type: Used as part of the ETo calculation to compensate for different types of ground cover.  Default is 0.23

To get an API key, register at www.darksky.net.  


### Node Settings
The settings for this node are:

#### Short Poll
   * Query DarkStar server for observation data
#### Long Poll
   * Not used


## Requirements

1. Polyglot V2 itself should be run on Raspian Stretch.
  To check your version, ```cat /etc/os-release``` and the first line should look like
  ```PRETTY_NAME="Raspbian GNU/Linux 9 (stretch)"```. It is possible to upgrade from Jessie to
  Stretch, but I would recommend just re-imaging the SD card.  Some helpful links:
   * https://www.raspberrypi.org/blog/raspbian-stretch/
   * https://linuxconfig.org/raspbian-gnu-linux-upgrade-from-jessie-to-raspbian-stretch-9
2. This has only been tested with ISY 5.0.13 so it is not guaranteed to work with any other version.

# Upgrading

Open the Polyglot web page, go to nodeserver store and click "Update" for "DarkSky".

For Polyglot 2.0.35, hit "Cancel" in the update window so the profile will not be updated and ISY rebooted.  The install procedure will properly handle this for you.  This will change with 2.0.36, for that version you will always say "No" and let the install procedure handle it for you as well.

Then restart the DarkSky nodeserver by selecting it in the Polyglot dashboard and select Control -> Restart, then watch the log to make sure everything goes well.

The DarkSky nodeserver keeps track of the version number and when a profile rebuild is necessary.  The profile/version.txt will contain the DarkSky profile_version which is updated in server.json when the profile should be rebuilt.

# Release Notes

- 2.0.2 03/17/2020
   - Add additional data drivers to forecast data
   - Re-organize the temperature drivers
   - Evaptranspiration units based on user preference
- 2.0.1 02/09/2020
   - Workaround bug in cloud polyglot
- 2.0.0 01/13/2020
   - Resign the code base to be more module
   - Improve handling of custom configuration parameters
   - Add ability to set logging level
- 1.1.6 10/13/2019
   - Add preciptation rate and chance of preciptiation
- 1.1.5 09/05/2019
   - Trap http request errors.
- 1.1.4 07/12/2019
   - Fix editor profile file ET entry.
- 1.1.3 06/21/2019
   - Fix bug introduced with previous change
- 1.1.2 06/20/2019
   - Add exeption handling to forecast data processing
- 1.1.1 04/19/2019
   - Fix spelling error for forecast node titles
- 1.1.0 04/16/2019
   - Add evapotranspiration calculations to forecast data.
   - Only send data when it has changed.
- 1.0.2 04/02/2019
   - Rework unit code and fix requirments for cloud Polyglot.
- 1.0.1 04/01/2019
   - Actually use the units configuration value in the query.
- 1.0.0 03/29/2019
   - Added to the node server store
- 0.0.1 12/27/2018
   - Initial version published to github
