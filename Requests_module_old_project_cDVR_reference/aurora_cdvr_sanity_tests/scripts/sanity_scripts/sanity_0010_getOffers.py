#!/usr/bin/python

import os
import sys
from pprint import pprint
import time
import requests
import json
import mypaths
from readYamlConfig import readYAMLConfigs
from getCatalogServices import getCdvrServiceIds
from L1commonFunctions import *

# need to eventually update households with authorizations
#  "authorizations": {"subscriptions":    [
#                                          {
#                                             "authorizationId": "41",
#                                             "authorizationType": "SUBSCRIPTION"
#                                          },
#

##########################################################################
#   Get cdvr subscription offers
##########################################################################

abspath = os.path.abspath(__file__)
scriptName = os.path.basename(__file__)
(test, ext) = os.path.splitext(scriptName)

def doit(cfg, printflg=False):
    try :
        print "Starting test " + test
        name = (__file__.split('/'))[-1]
        I = 'Core DVR Functionality'     #rally initiatives  
        US = 'Get cdvr subscription offers'
        TIMS_testlog = []
        TIMS_testlog = [name,I,US]
        disable_warning()   #Method Called to suppress all warnings
        cdvrOffers =  getCdvrSubscriptionOffers( cfg ) 
        if cdvrOffers != None:
            if len(cdvrOffers) > 0:
                if printflg:
                    pprint(cdvrOffers)
                msg = 'Testcase passed : cdvr offers fetched successfully.'
                print msg
                TIMS_testlog.append(0)
                TIMS_testlog.append(msg)
                return TIMS_testlog
            else:
                msg = "Testcase failed :No subscription offers found for cdvr services"
                print msg
                TIMS_testlog.append(1)
                TIMS_testlog.append(msg)
                return TIMS_testlog
        msg = "Testcase failed :cdvr offers could not be fetched."
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



def getCdvrSubscriptionOffers(cfg):
    '''
    getCdvrSubscriptionOffers(cfg)

    cfg is the parsed yaml config dictionary

    return None if some problem
    returns a list containing the subscription offers available on cdvr services (could be empty)

    '''

    # set values based on config
    protocol = cfg['protocol']
    hosts = [cfg['cmdc']['host']]
    if cfg['sanity']['allinstances'] == True and cfg['cmdc'].get('instances'):
        for k,v in cfg['cmdc']['instances'].items():
            hosts.append(v)

    port = str(cfg['cmdc']['port'])
    catalogueId = str(cfg['catalogueId'])
    caSystemId = str(cfg['caSystemId'])

    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25

    #pprint(hosts)

    cdvrServiceIds = getCdvrServiceIds(cfg)
    if cdvrServiceIds :
        print "cdvr services are successfully retrieved"
    else:
        print "unable to get cdvr services"
        return(None)
    serviceIdsCsv = ",".join(cdvrServiceIds)

    for index, host in enumerate(hosts):

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )

        url = protocol + "://" + host + ":" + port + "/cmdc/service/" + serviceIdsCsv + "/offers?catalogueId=" + catalogueId + "&caSystemId=" + caSystemId + "&count=255"

        print url
        r = requests.get(url)
        if r.status_code != 200:
            print "Problem accessing: " + url
            print r.status_code
            print r.headers
            print r.content
            return(None)

    # obviously only care about the last cmdc service retrieval (hope that's ok!)
    cdvrOffers = []
    try:
        offers = json.loads(r.text)['offers']
        for offer in offers:
            if offer['type'] == "subscription":
                cdvrOffers.append( offer['id'] )
    except:
        print test + " failed to get offers from cmdc"
        return(None)
    if cdvrOffers == []:
       print "### DEBUG STARTED ### \n\n"
       offers = json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
       print offers
       print "### DEBUG ENDED ### \n\n"

    return(cdvrOffers)

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

