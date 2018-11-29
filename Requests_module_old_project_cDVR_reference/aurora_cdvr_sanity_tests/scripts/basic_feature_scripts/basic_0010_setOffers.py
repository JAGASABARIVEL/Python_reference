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
    print "Starting test " + test
    return( setCdvrSubscriptionOffers( cfg )  )

def setCdvrSubscriptionOffers(cfg):
    '''
    setCdvrSubscriptionOffers(cfg)

    cfg is the parsed yaml config dictionary

    return 1 if some problem
    returns 0 if ok

    '''

    offers = getCdvrSubscriptionOffers(cfg)
    if offers == None:
        return 1

    # set values based on config
    prefix = cfg['basic_feature']['household_prefix']
    protocol = cfg['protocol']
    hosts = [cfg['upm']['host']]
    if cfg['basic_feature']['allinstances'] == True and cfg['upm'].get('instances'):
        for k,v in cfg['upm']['instances'].items():
            hosts.append(v)

    port = str(cfg['upm']['port'])

    households_needed = cfg['basic_feature']['households_needed']
    throttle_milliseconds = cfg['basic_feature']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25

    headers = {
        'Content-Type': 'application/json',
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
    }

    #pprint(hosts)

    cdvrServiceIds = getCdvrServiceIds(cfg)

    serviceIdsCsv = ",".join(cdvrServiceIds)

    for host in hosts:
     for index in range(households_needed):
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
                return(1)
    return(0)

if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    #read config file 
    sa = sys.argv
    cfg = relative_config_file(sa,scriptName)
    if cfg['basic_feature']['print_cfg']:
         print "\nThe following configuration is being used:\n"
         pprint(cfg)
         print
    exit( doit(cfg, True) )

