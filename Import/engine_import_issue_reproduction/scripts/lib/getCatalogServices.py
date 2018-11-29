#!/usr/bin/python

import os
import sys
from readYamlConfig import readYAMLConfigs
from pprint import pprint
import time
import requests
import json

##########################################################################
#   Get cdvr services
##########################################################################

abspath = os.path.abspath(__file__)
scriptName = os.path.basename(__file__)
(test, ext) = os.path.splitext(scriptName)

def doit(cfg, printflg=False):
    print "Starting test " + test
    cdvrServices =  getCdvrServiceIds( cfg ) 
    if cdvrServices != None:
        if len(cdvrServices) > 0:
            if printflg:
                pprint(cdvrServices)
            return(0)
        else:
            print "No services with cdvrAvailable flag set"
    return(1)

def getCdvrServiceIds(cfg):
    '''
    getCdvrServiceIds(cfg)

    cfg is the parsed yaml config dictionary

    return None if some problem
    returns a list containing the service id's of cdvrAvailable services (could be empty)

    '''

    # set values based on config
    protocol = cfg['protocol']
    hosts = [cfg['cmdc']['host']]
    if cfg['sanity']['allinstances'] == True and cfg['cmdc'].get('instances'):
        for k,v in cfg['cmdc']['instances'].items():
            hosts.append(v)

    port = cfg['cmdc']['port']
    region = cfg['region']
    cmdcRegion = cfg['cmdcRegion']

    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25

    #pprint(hosts)

    for index, host in enumerate(hosts):

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )

        url = protocol + "://" + host + ":" + str(port) + "/cmdc/services/?region=" + str(region) + "&count=23"

        r = requests.get(url)
        if r.status_code != 200:
            print "Problem accessing: " + url
            print r.status_code
            print r.headers
            print r.content
            return(None)

    # obviously only care about the last cmdc service retrieval (hope that's ok!)
    cdvrServices = []
    cdvrServices1 = []
    try:
        services = json.loads(r.text)['services']
        for service in services:
            if service['cdvrAvailable'] == True:
                cdvrServices.append( service['id'] )
            #print service['cdvrAvailable']
    except:
        print test + " failed to get services with cdvr flag set "
        return(None)
    #cdvrServices1 = "28506,42642"
    return(cdvrServices)

if __name__ == '__main__':
    # Find our current dir and set our base dir
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    scriptDir = os.path.dirname(abspath)
    # Trim off the scripts dir
    baseDir, null = os.path.split(scriptDir)

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
        if cfg['sanity']['print_cfg']:
            print "\nThe following configuration is being used:\n"
            pprint(cfg)
            print
    else:
        print 'Error reading configs'
        sys.exit(1)

    exit( doit(cfg, True) )

