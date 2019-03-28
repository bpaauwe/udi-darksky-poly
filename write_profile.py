#!/usr/bin/env python3

import collections
import re
import os
import zipfile
import json

pfx = "profile:"

VERSION_FILE = "profile/version.txt"

# templates to make the string writes a bit easier to read
NODEDEF_TMPL = "  <nodeDef id=\"%s\" nodeType=\"139\" nls=\"%s\">\n"
STATUS_TMPL = "      <st id=\"%s\" editor=\"%s\" />\n"

# unit of measure to editor mapping
uom = {
        4 : 'TEMP_C',
        17 : 'TEMP_F',
        2 : 'bool',
        22 : 'PERCENT',
        117 : 'MB',
        48 : 'MPH',
        49 : 'MPS',
        76 : 'DEGREES',
        0 : 'INCHES',
        82 : 'MM',
        36 : 'LUMIN',
        56 : 'int',
        38 : 'METERS',
        27 : 'COVERAGE',
        70 : 'INTENSITY',
        25 : 'CONDITIONS',
        118 : 'HPA',
        23 : 'INHG',
        71 : 'UV',
        116 : 'MILES',
        46 : 'mmhr',
        24 : 'inhr',
        }


# Create a node definition file.
# 
# We're assuming that we're just creating the definition for the controller
# node and that to do that, we just iterate through the driver list to
# build the status section of the node definition.
def write_profile(logger, drivers):
    sd = get_server_data(logger)
    if sd is False:
        logger.error("Unable to complete without server data...")
        return False

    logger.info("{0} Writing profile/nodedef/nodedef.xml".format(pfx))
    if not os.path.exists("profile/nodedef"):
        try:
            os.makedirs("profile/nodedef")
        except:
            LOGGER.error('unable to create node definition directory.')

    # Write the node definition file
    nodedef = open("profile/nodedef/nodedef.xml", "w")
    nodedef.write("<nodeDefs>\n")

    nodedef.write(NODEDEF_TMPL % ('dsweather', 'dsk'))
    nodedef.write("    <editors />\n")
    nodedef.write("    <sts>\n")
    for d in drivers:
        nodedef.write(STATUS_TMPL % (d['driver'], uom[d['uom']]))
    nodedef.write("    </sts>\n")
    nodedef.write("    <cmds>\n")
    nodedef.write("      <sends />\n")
    nodedef.write("      <accepts>\n")
    nodedef.write("        <cmd id=\"DISCOVER\" />\n")
    nodedef.write("        <cmd id=\"REMOVE_NOTICES_ALL\" />\n")
    nodedef.write("        <cmd id=\"UPDATE_PROFILE\" />\n")
    nodedef.write("      </accepts>\n")
    nodedef.write("    </cmds>\n")
    nodedef.write("  </nodeDef>\n\n")
    nodedef.write("</nodeDefs>")

    nodedef.close()

    # Update the profile version file with the info from server.json
    with open(VERSION_FILE, 'w') as outfile:
        outfile.write(sd['profile_version'])
    outfile.close()

    # Create the zip file that can be uploaded to the ISY
    write_profile_zip(logger)

    logger.info(pfx + " done.")


def write_profile_zip(logger):
    src = 'profile'
    abs_src = os.path.abspath(src)
    with zipfile.ZipFile('profile.zip', 'w') as zf:
        for dirname, subdirs, files in os.walk(src):
            # Ignore dirs starint with a dot, stupid .AppleDouble...
            if not "/." in dirname:
                for filename in files:
                    if filename.endswith('.xml') or filename.endswith('txt'):
                        absname = os.path.abspath(os.path.join(dirname, filename))
                        arcname = absname[len(abs_src) + 1:]
                        logger.info('write_profile_zip: %s as %s' %
                                (os.path.join(dirname, filename), arcname))
                        zf.write(absname, arcname)
    zf.close()


def get_server_data(logger):
    # Read the SERVER info from the json.
    try:
        with open('server.json') as data:
            serverdata = json.load(data)
    except Exception as err:
        logger.error('get_server_data: failed to read {0}: {1}'.format('server.json',err), exc_info=True)
        return False
    data.close()

    # Get the version info
    try:
        version = serverdata['credits'][0]['version']
    except (KeyError, ValueError):
        logger.info('Version not found in server.json.')
        version = '0.0.0.0'
    # Split version into two floats.
    sv = version.split(".");
    v1 = 0;
    v2 = 0;
    if len(sv) == 1:
        v1 = int(v1[0])
    elif len(sv) > 1:
        v1 = float("%s.%s" % (sv[0],str(sv[1])))
        if len(sv) == 3:
            v2 = int(sv[2])
        else:
            v2 = float("%s.%s" % (sv[2],str(sv[3])))
    serverdata['version'] = version
    serverdata['version_major'] = v1
    serverdata['version_minor'] = v2
    return serverdata

# If we wanted to call this as a stand-alone script to generate the profile
# files, we'd do something like what's below but we'd need some way to 
# set the configuration.

if __name__ == "__main__":
    import logging,json
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=10,
        format='%(levelname)s:\t%(name)s\t%(message)s'
    )
    logger.setLevel(logging.DEBUG)

    # Test dictionaries to generate a custom nodedef file.

    # Only write the profile if the version is updated.
    sd = get_server_data(logger)
    if sd is not False:
        local_version = None
        try:
            with open(VERSION_FILE,'r') as vfile:
                local_version = vfile.readline()
                local_version = local_version.rstrip()
                vfile.close()
        except (FileNotFoundError):
            pass
        except (Exception) as err:
            logger.error('{0} failed to read local version from {1}: {2}'.format(pfx,VERSION_FILE,err), exc_info=True)

        if local_version == sd['profile_version']:
            logger.info('{0} Not Generating new profile since local version {1} is the same current {2}'.format(pfx,local_version,sd['profile_version']))
        else:
            logger.info('{0} Generating new profile since local version {1} is not current {2}'.format(pfx,local_version,sd['profile_version']))
            #write_profile(logger, [])
