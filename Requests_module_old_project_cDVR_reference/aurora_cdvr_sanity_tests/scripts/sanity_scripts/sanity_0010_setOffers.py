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
from getOffers import getCdvrSubscriptionOffers
from L1commonFunctions import *

# need to eventually update households with authorizations
#  "authorizations": {"subscriptions":    [
#                                          {
#                                             "authorizationId": "41",
#                                             "authorizationType": "SUBSCRIPTION"
#                                          },
#

##########################################################################
#   Set cdvr subscription offers
##########################################################################

abspath = os.path.abspath(__file__)
scriptName = os.path.basename(__file__)
(test, ext) = os.path.splitext(scriptName)

def doit(cfg, printflg=False):
    try :
        print "Starting test " + test
        name = (__file__.split('/'))[-1]
        I = 'Core DVR Functionality'     #rally initiatives  
        US = 'Set cdvr subscription offers'
        TIMS_testlog = []
        TIMS_testlog = [name,I,US]
        disable_warning()   #Method Called to suppress all warnings
        #return( setCdvrSubscriptionOffers( cfg )  )
        #return_code =  return( setCdvrSubscriptionOffers( cfg )  )
        if (setCdvrSubscriptionOffers( cfg )  ) == 0:
            msg = 'Testcase passed : Set cdvr subscription offers is successfully executed '
            print msg
            TIMS_testlog.append(0)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            msg = 'Testcase failed :Set cdvr subscription offers is not successfully executed '
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



def setCdvrSubscriptionOffers(cfg):
    '''
    setCdvrSubscriptionOffers(cfg)

    cfg is the parsed yaml config dictionary

    return 1 if some problem
    returns 0 if ok

    '''

    offers = getCdvrSubscriptionOffers(cfg)
    if offers == None:
        msg = 'Error in retrieving offers for subscription'
        print msg
        return 1

    # set values based on config
    prefix = cfg['sanity']['household_prefix']
    protocol = cfg['protocol']
    hosts = [cfg['upm']['host']]
    if cfg['sanity']['allinstances'] == True and cfg['upm'].get('instances'):
        for k,v in cfg['upm']['instances'].items():
            hosts.append(v)

    port = str(cfg['upm']['port'])

    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25

    headers = {
        'Content-Type': 'application/json',
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
    }

    #pprint(hosts)

    cdvrServiceIds = getCdvrServiceIds(cfg)
    if cdvrServiceIds :
        print "cdvr services are successfully retrieved"
    else:
        print "unable to get cdvr services"
        return 1

    serviceIdsCsv = ",".join(cdvrServiceIds)

    for index, host in enumerate(hosts):

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )

        householdid = prefix + str(index)

        for offerid in offers:
            payload = """
            {
                "authorizationId": "%s",
                "authorizationType": "SUBSCRIPTION"
            }
            """ % offerid
            url = protocol + "://" + host + ":" + port + "/upm/households/" + householdid + "/authorizations/subscriptions/" + str(offerid)
            print url
            r = requests.put(url, headers=headers, data=payload)
            if r.status_code != 201 and r.status_code != 200:
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
                msg = 'Testcase failed :Problem accessing in url' 
                print msg
                return(1)
    return(0)

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

