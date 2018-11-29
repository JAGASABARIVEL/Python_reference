#!/usr/bin/python

"""
Read YAML config files and return single object of the merged contents or None
"""

# Based on work done by Joby Bett - Cisco 2015
#
# Ken Shaffer - Cisco Systems Inc, 2015

import os
import sys
import yaml
from pprint import pprint
from logger import enable_logging

# courtesy of http://stackoverflow.com/questions/823196/yaml-merge-in-python
def _merge(new, current):
    if isinstance(new, dict) and isinstance(current, dict):
        for k,v in current.iteritems():
            if k not in new:
                new[k] = v
            else:
                new[k] = _merge(new[k],v)
    return new

def readYAMLConfigs(labName, IPOverRideFile=None):
    enable_logging()
    """

        Reads ../config/config.yaml for default config
        Reads ../config/labName/config.yaml if present for any overrides
        Reads ../config/labName/ips.yaml for lab IP config
        Reads optional IPOverRideFile (also a .yaml file) for any IP overrides

        Returns merged object of all configs in that order

        Return None on error and prints error message

    """
    # Find our current dir and set our base dir
    abspath = os.path.abspath(__file__)
    scriptDir = os.path.dirname(abspath)
    # Trim off the scripts dir
    baseDir, null = os.path.split(scriptDir)

    # base config filename
    baseConfigFile = 'config.yaml'

    # per lab ip config filename
    ipConfigFile = 'ips.yaml'

    # config dir
    slashConfigDirSlash = '/config/'
    try:
        opened_file = open(baseDir + slashConfigDirSlash + baseConfigFile)
    except IOError as err:
        slashConfigDirSlash = '/../config/'
        opened_file = open(baseDir + slashConfigDirSlash + baseConfigFile)

    baseConfig = yaml.safe_load(opened_file)

    # Load our lab config
    if os.path.isdir(baseDir + slashConfigDirSlash + labName):
        labFileName = baseDir + slashConfigDirSlash + labName + '/' + ipConfigFile 
        if os.path.isfile(labFileName):
            labIps = yaml.safe_load(open(labFileName))
        else:
            print "ERROR: lab ips.yaml (%s) does not exist" % labFileName
            return None
        labFileName = baseDir + slashConfigDirSlash + labName + '/' + baseConfigFile
        labConfig = None
        if os.path.isfile(labFileName):
            labConfig = yaml.safe_load(open(labFileName))
        localFileName = scriptDir + '/' + baseConfigFile
        localConfig = None
        if os.path.isfile(localFileName):
            localConfig = yaml.safe_load(open(localFileName))
        else:
            localFileName = scriptDir + '/../' + baseConfigFile
            if os.path.isfile(localFileName):
                localConfig = yaml.safe_load(open(localFileName))
    else:
        print "ERROR: no such lab named %s exists" % labName
        return None

    vmConfig = None
    if IPOverRideFile:
        if os.path.isfile(IPOverRideFile):
            vmConfig = yaml.safe_load(open(IPOverRideFile))
        else:
            print "ERROR: %s does not exist" % IPOverRideFile
            return None

    # at this point should have 3 configs loaded, possibly 4, merge into one
    if baseConfig is None:
        baseConfig = {}
    if labIps is None:
        labIps = {}
    if vmConfig is None:
        vmConfig = {}
    if labConfig is None:
        labConfig = {}
    if localConfig is None:
        localConfig = {}

    currentConfig = _merge(labConfig, baseConfig)
    currentConfig = _merge(labIps, currentConfig)
    currentConfig = _merge(localConfig, currentConfig)
    currentConfig = _merge(vmConfig, currentConfig)

    return currentConfig

if __name__ == '__main__':
    # Find our current dir and set our base dir
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)

    # valid arg count?
    sa = sys.argv
    lsa = len(sys.argv)
    if lsa != 3  and lsa != 2:
        print "Usage: [ python ] %s <lab name> [ <ip_override.yaml> ] " % scriptName
        print "Example: [ python ] %s lwr_integration deployed_vms.yaml" % scriptName
        print "         [ python ] %s lwr_integration " % scriptName
        print "  where lwr_integration is a directory under ./config expected to contain ips.yaml"
        print "        deployed_vms.yaml is an optional yaml file of components and their hosts/ips"
        print "        similar to ips.yaml in form (see config/README file for example)"
        print 
        print " the content of the 2nd arg if provided overrides the same content if present "
        print " in content of 1st arg"
        sys.exit(1)

    labName = sa[1]
    vmInfo = None
    if lsa > 2:
        vmInfo = sa[2]

    cfg = readYAMLConfigs(labName, vmInfo)
    if cfg:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
        print
    else:
        print 'Error reading configs'
        sys.exit(1)

