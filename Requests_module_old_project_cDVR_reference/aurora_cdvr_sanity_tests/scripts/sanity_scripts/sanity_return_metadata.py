#!/usr/bin/python

import os
import sys
from pprint import pprint
import time
import requests
import json
import random
import itertools
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
##########################################################################
#   Return metadata for single channel
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
    US = 'Return metadata for single channel'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    # set values based on config
    protocol = cfg['protocol']
    cmdc_hosts = get_hosts_by_config_type(cfg,'cmdc',printflg)
    hc_hosts = get_hosts_by_config_type(cfg,'hc',printflg)
    region = cfg['region']
    port1 = cfg['hc']['port']
    port2 = cfg['cmdc']['port'] 
    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25
    if cmdc_hosts == None or hc_hosts == None: #returns 1 if there is a mismatch host name or hostname not present
        msg = 'Testcase failed : cmdc Host not found'
        print msg
        TIMS_testlog.append(1)
        TIMS_testlog.append(msg)
        return TIMS_testlog
        
    headers = {
        'Accept': 'application/json',
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
        }
    timeout = 2
    any_host_pass = 0
    maphosts = list(itertools.product(cmdc_hosts,hc_hosts))
    printLog("Final list :"+ str(maphosts),printflg=False)
    for (cmdc_hosts,hc_hosts) in maphosts :
        time.sleep(throttle_milliseconds / 1000.0 )
        serviceid_response= fetch_serviceIdbyregion(protocol,cmdc_hosts,port2,region,timeout)
        serviceids = get_serviceIdlist(serviceid_response)
        if not serviceids :
            print "serviceID list not present" 
        else:
            channel = random.choice(serviceids)
            url = protocol + "://" + hc_hosts + ":" + str(port1) + "/mdp/channels?filter:channel=" + str(channel) + "&sourceType=uhe&targetType=uhe&pset=mdp:no-channel&region=" + str(region) 
            print "Get Metadata via " + url
            r = sendURL ("get",url,timeout,headers)
            if r is not None :
                if ( r.status_code != 200):
                    print "Problem accessing: " + url
                    print r.status_code
                    print r.headers
                    print r.content
                else:
                    if r.content is None :
                        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                        print "Metadata for randomly picked channel "+channel+" \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                    any_host_pass = any_host_pass + 1
                    printLog("Metadata for randomly picked channel "+channel+" \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)


    if any_host_pass :
         msg = 'Testcase passed :Return metadata for single channel ran successfully.'
         print msg
         TIMS_testlog.append(0)
         TIMS_testlog.append(msg)
         return TIMS_testlog

    else:
         msg = 'Testcase failed :Return metadata for single channel was not successful.'
         print msg
         TIMS_testlog.append(1)
         TIMS_testlog.append(msg)
         return TIMS_testlog

#return(0)

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
                                                            
