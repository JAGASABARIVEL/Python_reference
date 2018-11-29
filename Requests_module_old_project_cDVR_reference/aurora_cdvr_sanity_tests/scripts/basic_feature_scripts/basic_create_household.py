#!/usr/bin/python
'''
Create a household for each upm host in configuration
'''

import os
import sys
from pprint import pprint
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *

##########################################################################
#   Function to create actual household
#
#   Return True on success, else False
##########################################################################
def _create_household(household_index,host,cfg):
    '''
    Internal function to do the actual creation

    _create_household(idx, host, cfg)

    args:
        idx is index number used for the name of the household
        host is the IP/hostname to send create request to
        cfg is the configuration dictionary

    returns True on success, else False
    '''

    # set values based on config
    protocol = cfg['protocol']
    port = cfg['upm']['port']
    prefix = cfg['basic_feature']['household_prefix']
    region = cfg['region']
    cmdcRegion = cfg['cmdcRegion']
    adZone = cfg['adZone']
    marketingTarget = cfg['marketingTarget']
    enabledServices = '"{0}"'.format('", "'.join(cfg['enabledServices']))

    headers = {
        'Content-Type': 'application/json',
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
    }
    householdid = prefix + str(household_index)
    deviceid = householdid + 'd'
    payload = """
    {
      "householdId" : "%s",
      "householdStatus" : "ACTIVATED",
      "operateStatus": "ACTIVE",
      "locale" : {
            "region" : "%s",
            "cmdcRegion":"%s",
            "adZone": "%s",
                "marketingTarget": "%s"
                 },
    "enabledServices" : [%s],
    "devices": [   {
                "bssFullType": "cDVR_MANAGED",
                "operateStatus": "ACTIVE",
                "deviceId": "%s",
                "ipAddress": "10.1.1.15"
                }]
    }
    """ % (householdid, region, cmdcRegion, adZone, marketingTarget, enabledServices, deviceid)

    #print payload

    url = protocol + "://" + host + ":" + str(port) + "/upm/households/" + householdid

    if _household_exists(url):
        print "Household already present: " + url
        result = True
    else:
        print "Create household via " + url
        #print headers
        try:
            r = requests.put(url, data=payload, headers=headers, timeout=10)
            if r.status_code != 201:
                print r.status_code
                print r.headers
                print r.content
                result = False
            else:
                result = True
        except:
            print "  Error: timeout "
            result = False
    return result


##########################################################################
#   Function to check if household exists
##########################################################################

def _household_exists(url):
    headers = {
        'Source-Type' : 'WEB',
        'Source-ID'   : '127.0.0.1',
        'Accept'      : 'application/json',
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            result = True
        else:
            result = False
    except:
        result = False
    return result

##########################################################################
#   Create a household
##########################################################################

def doit(cfg, printflg=False):

    '''
    Create one or more households based on configuration. Checks if household
    already exists, and if so, assumes good as is.

    The doit(cfg) function is called by the main sanity script and the yaml
    parsed config is passed in as a dictionary.

    The yaml config must have the following defined:

       protocol: http   # example, could be https
       upm:
            host: <IP or hostname>
            port: <upm port to use>
            instances:    # optional
                upm1: <IP or hostname>
                upm2: <IP or hostname>
       sanity:
            allinstances: True   # or False (False if to skip those hosts defined
                                             under instances if instances block
                                             defined)
            household_prefix: <string>   # a prefix to use in household creation/references
            throttle_milliseconds: <number> # the number of milliseconds to use when waiting 
            print_cfg: True  # to print the yaml configuration dictionary after load, else False (used by main)
       region: <some region id>
       cmdcRegion: <some cmdc region>  # typically the same as region
       adZone: <string>
       marketingTarget: <string>  # typically the same as adZone
       enabledServices:
            - <service1>
            - <service2>
            ...

    '''

    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test

    # set values based on config
    households_needed = cfg['basic_feature']['households_needed']
    hosts = get_hosts_by_config_type(cfg, 'upm', printflg)

    throttle_milliseconds = cfg['basic_feature']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25


    #pprint(hosts)

    for index, host in enumerate(hosts):

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )

            if index % 4 == 0:
                print "waiting a few seconds in an effort for PVR creation to catch up before 1st use"
                time.sleep(2)   # give some time for PVRs to be created

        if _create_household(index, host, cfg) == False:
            return(1)

    # create the rest using the first host
    while index + 1 < households_needed:
        index = index + 1

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )

            if index % 4 == 0:
                print "waiting a few seconds in an effort for PVR creation to catch up before 1st use"
                time.sleep(2)   # give some time for PVRs to be created

        if _create_household(index, hosts[0], cfg) == False:
            return(1)

    print "waiting a few seconds in an effort for PVR creation to catch up before 1st use"
    time.sleep(4)   # give some time for PVRs to be created
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
    exit( doit(cfg, True) )

