#!/usr/bin/python
import json 
import os
import sys
from pprint import pprint
import calendar
import requests
import ast
import time
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
##########################################################################
#   Get Schedules/ GridRequest
##########################################################################

def doit(cfg,printflg=False):
    disable_warning()   #Method Called to suppress all warnings
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'Get Schedules/ GridRequest'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    # set values based on config
    protocol = cfg['protocol']
    hosts = get_hosts_by_config_type(cfg,'cmdc',printflg)
    port = cfg['cmdc']['port']
    prefix = cfg['sanity']['household_prefix']
    region = cfg['region']
    catalogueId = cfg['catalogueId']
    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25
    headers = {
        'Accept': 'application/json',
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
    }
    timeout = 2
    any_host_pass = 0
    for index, host in enumerate(hosts):

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )
        householdid = prefix + str(index)
        deviceid = householdid + 'd'
        #Epoch Time Calculation
        timewindows = epochtime()
        #Getting Service Id Lists
        serviceid_response= fetch_serviceIdbyregion(protocol,host,port,region,timeout)
        serviceids = get_serviceIdlist(serviceid_response)

        serviceidlist = ','.join(serviceids)
        if not serviceids :
            print "serviceID list not present"
        else :
            url = protocol + "://" + host + ":" + str(port) +"/cmdc/services/schedule/"+ timewindows  + "?lang=eng&serviceList="+ serviceidlist +"&count=255&region="+ str(region) +"&catalogueId=" + str(catalogueId)
            print "CMDC Schedule details fetched via %s"%url
            r = sendURL ("get",url,timeout,headers)
            if r is not None :
                if ( r.status_code != 200):
                    print "Problem accessing: " + url
                    print r.status_code
                    print r.headers
                    print r.content
                else:
                    any_host_pass = any_host_pass + 1
                    printLog("\nList of channels %s"%serviceidlist,printflg)
                    try:
                        services = json.loads(r.text)['services']
                        for service in services:
                            if service['cdvrAvailable'] == True:
                                 any_host_pass = any_host_pass + 1
                                 printLog("\ncDVR enabled for service Id %s - Events are recordable"%service['id'],printflg)
                            else:
                                 print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                                 print '\n get all schedule :'+ json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                                 print "\ncDVR Not enabled for service Id %s - Events are Not recordable"%service['id']
                                 print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                    except:
                           printLog(" failed to get services with cdvr flag set",printflg)

    if any_host_pass :
         msg = 'Testcase passed : Get Schedules/ GridRequest ran successfully.'
         print msg
         TIMS_testlog.append(0)
         TIMS_testlog.append(msg)
         return TIMS_testlog

    else:
         msg = 'Testcase failed :Get Schedules/ GridRequest was not successful.'
         print msg
         TIMS_testlog.append(1)
         TIMS_testlog.append(msg)
         return TIMS_testlog
if  __name__ == '__main__':
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
