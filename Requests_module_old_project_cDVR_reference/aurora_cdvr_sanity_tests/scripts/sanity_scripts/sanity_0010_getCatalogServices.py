#!/usr/bin/python

import os
import sys
from pprint import pprint
import time
import requests
import json
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *

##########################################################################
#   Get cdvr services
##########################################################################

abspath = os.path.abspath(__file__)
scriptName = os.path.basename(__file__)
(test, ext) = os.path.splitext(scriptName)

def doit(cfg, printflg=False):
    try :
        print "Starting test " + test
        name = (__file__.split('/'))[-1]
        I = 'Core DVR Functionality'     #rally initiatives  
        US = 'Get cdvr services'
        TIMS_testlog = []
        TIMS_testlog = [name,I,US]
        disable_warning()   #Method Called to suppress all warnings
        cdvrServices =  getCdvrServiceIds( cfg ) 
        if cdvrServices != None:
            if len(cdvrServices) > 0:
                if printflg:
                    pprint(cdvrServices)
                msg = 'Testcase passed : cdvr services fetched successfully'
                print msg
                TIMS_testlog.append(0)
                TIMS_testlog.append(msg)
                return TIMS_testlog
            else:
                msg = "Testcase failed : No services with cdvrAvailable flag set"
                print msg
                TIMS_testlog.append(1)
                TIMS_testlog.append(msg)
                return TIMS_testlog
        msg = 'Testcase failed : cdvr services are not available'
        print msg
        TIMS_testlog.append(1)
        TIMS_testlog.append(msg)
        return TIMS_testlog
    except:
        msg = "Testcase failed : Error Occurred in Script: " + PrintException(True)
        print msg
        TIMS_testlog.append(1)
        TIMS_testlog.append(msg)
        return TIMS_testlog


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
    try:
        services = json.loads(r.text)['services']
        for service in services:
            if service['cdvrAvailable'] == True:
                cdvrServices.append( service['id'] )
    except:
        print test + " failed to get services with cdvr flag set "
        return(None)
    if cdvrServices == []:
       print "### DEBUG STARTED ### \n\n"
       services = json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
       print services
       print "### DEBUG ENDED ### \n\n"
    return(cdvrServices)

if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    #read config file 
    sa = sys.argv
    cfg = relative_config_file(sa,scriptName)
    if cfg['sanity']['print_cfg']:
         print "\nThe following configuration is being used:\n"
         pprint(cfg)
         print
    L = doit(cfg, True)
    exit(L[3] )

