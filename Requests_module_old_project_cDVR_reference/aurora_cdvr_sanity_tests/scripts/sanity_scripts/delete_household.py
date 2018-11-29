#!/usr/bin/python

import os
import sys
from pprint import pprint
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *

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
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            result = True
        else:
            result = False
    except:
        result = False
    return result

##########################################################################
#   Delete a household
##########################################################################
def _delete_household(household_index,host,cfg):
    # set values based on config
    protocol = cfg['protocol']

    port = cfg['upm']['port']
    prefix = cfg['sanity']['household_prefix']

    headers = {
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
    }

    householdid = prefix + str(household_index)
    url = protocol + "://" + host + ":" + str(port) + "/upm/households/" + householdid


    #print headers

    result = True
    if _household_exists(url):
        print "delete via " + url
        try:
            r = requests.delete(url, headers=headers, timeout=15)
            if r.status_code == 202:
                print "server handling this asynchronously"
                print r.headers
                print "essentially need to loop while 202, then done"
                print "TBD: handle later"
                result = True
            elif r.status_code != 200:
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

def doit(cfg, printflg=False):

    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    disable_warning()   #Method Called to suppress all warnings
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'Delete household'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    if not cfg['sanity']['delete_household']:
        TIMS_testlog.append(0)
        msg = 'Testcase passed :Household deletion skipped'
        TIMS_testlog.append(msg)
        print msg
        return TIMS_testlog
        

    hosts = get_hosts_by_config_type(cfg,'upm',printflg)

    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25

    households_needed = cfg['sanity']['households_needed']

    #pprint(hosts)

    for index, host in enumerate(hosts):

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )

            if index % 4 == 0:
                print "waiting a few seconds in an effort for PVR deletion to catch up"
                time.sleep(2)   # give some time for PVRs to be deleted

        if _delete_household(index, host, cfg) == False:
            msg = 'Testcase failed :Household not deleted'
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        
    # delete the rest using the first host
    while index + 1 < households_needed:
        index = index + 1

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )

            if index % 4 == 0:
                print "waiting a few seconds in an effort for PVR deletion to catch up"
                time.sleep(2)   # give some time for PVRs to be deleted

        if _delete_household(index, hosts[0], cfg) == False:
            msg = 'Testcase failed :Household not deleted'
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog

    print "waiting a few seconds in an effort for PVR deletion to catch up"
    time.sleep(4)   # give some time for PVRs to be deleted
    msg = 'Testcase passed :Household deleted'
    print msg
    TIMS_testlog.append(0)
    TIMS_testlog.append(msg)
    return TIMS_testlog

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

