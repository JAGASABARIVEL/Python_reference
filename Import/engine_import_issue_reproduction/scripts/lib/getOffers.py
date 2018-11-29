#!/usr/bin/python

import os
import sys
from readYamlConfig import readYAMLConfigs
from getCatalogServices import getCdvrServiceIds
from pprint import pprint
import time
import requests
import json

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
        print cdvrServiceIds
        print "cdvr services are successfully retrieved"
    else:
        print "unable to get cdvr services"
        return None


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

