#!/usr/bin/python

import os
import sys
from pprint import pprint
import time
import requests
import json
import mypaths
from readYamlConfig import readYAMLConfigs
from basic_0010_getCatalogServices import getCdvrServiceIds
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
    print "Starting test " + test
    cdvrOffers =  getCdvrSubscriptionOffers( cfg ) 
    if cdvrOffers != None:
        if len(cdvrOffers) > 0:
            if printflg:
                pprint(cdvrOffers)
            return(0)
        else:
            print "No subscription offers found for cdvr services"
    return(1)

def getCdvrSubscriptionOffers(cfg):

    # set values based on config
    protocol = cfg['protocol']
    hosts = [cfg['cmdc']['host']]
    if cfg['basic_feature']['allinstances'] == True and cfg['cmdc'].get('instances'):
        for k,v in cfg['cmdc']['instances'].items():
            hosts.append(v)

    port = str(cfg['cmdc']['port'])
    catalogueId = str(cfg['catalogueId'])
    caSystemId = str(cfg['caSystemId'])

    throttle_milliseconds = cfg['basic_feature']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25
    cdvrServiceIds = getCdvrServiceIds(cfg)
    serviceIdsCsv = ",".join(cdvrServiceIds)
    for index, host in enumerate(hosts):
        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )
        url = protocol + "://" + host + ":" + port + "/cmdc/service/" + serviceIdsCsv + "/offers?catalogueId=" + catalogueId + "&caSystemId=" + caSystemId + "&count=255"
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
            #print service['cdvrAvailable']
    except:
        print test + " failed to get offers from cmdc"
        return(None)
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
    exit( doit(cfg, True) )

