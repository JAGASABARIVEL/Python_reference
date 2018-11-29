#!/usr/bin/python
"""
This script is standalone. This reads 'versions.yaml' file
under specific lab and appends 'Versions' sections to 'ec_results.json'
file. This 'ec_results.json' is later interpreted by TIMS reporting to
pull data into TIMS.
"""

import os
import sys
import yaml
import mypaths
from pprint import pprint
from jsonReadWrite import JsonReadWrite
from readYamlConfig import readYAMLConfigs

def readYAMLVersions(labName):
    """
        Reads ../config/labName/versions.yaml 
        Return None on error and prints error message
    """	
    # Find our current dir and set our base dir
    abspath = os.path.abspath(__file__)
    scriptDir = os.path.dirname(abspath)
    # Trim off the scripts dir
    baseDir, null = os.path.split(scriptDir)

    
    # base config filename
    versionFile = 'versions.yaml'
    # config dir
    slashConfigDirSlash = '/config/'

    #Make sure we are in the right directory
    if not(os.path.isdir(baseDir + slashConfigDirSlash + labName)):
        slashConfigDirSlash = '/../config/'
        if not(os.path.isdir(baseDir + slashConfigDirSlash + labName)):
            print "ERROR: no such lab named %s exists" % labName
            return None

    labFileName = baseDir + slashConfigDirSlash + labName + '/' + versionFile
    if os.path.isfile(labFileName):
        labVersions = yaml.safe_load(open(labFileName))
    else:
        print "ERROR: lab versions.yaml (%s) does not exist" % labFileName
        return None

    return labVersions
    
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
        print "  where lwr_integration is a directory under ../config expected to contain ips.yaml"
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
        filename = cfg['test_results']['filename']
        vers = readYAMLVersions(labName)
        if vers:
            print "\nThe following Versions are being used:\n"
            pprint(vers)
            versions=vers['versions']
            print
        else:
            print 'Error reading Versions'
            sys.exit(1)

        
        results = JsonReadWrite(filename)
        versObj = {
		"config":{
			"versions":versions
		}
 		}
        results.writeDictJson(versObj)
    else:
        print 'Error reading configs'
        sys.exit(1)

