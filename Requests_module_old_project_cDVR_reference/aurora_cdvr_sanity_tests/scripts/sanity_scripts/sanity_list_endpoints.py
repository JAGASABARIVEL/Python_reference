#!/usr/bin/python

import os
import sys
import time
import requests
import json
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
##########################################################################
#   List endpoints from cluster
##########################################################################
def doit(cfg,printflg=False):
    # announce
    disable_warning()   #Method Called to suppress all warnings
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'List endpoints from cluster'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]
    if cfg['recording_api'] != 'msr':
        TIMS_testlog.append(2)
        msg = 'Testcase warning :This test only valid for msr.'
        TIMS_testlog.append(msg)
        print msg
        return TIMS_testlog
    # set values based on config
    protocol = cfg['protocol']
    hosts = get_hosts_by_config_type(cfg,'msr',printflg)
    if hosts == None :
        msg = 'Testcase failed :Host not found'
        print msg
        TIMS_testlog.append(1)
        TIMS_testlog.append(msg)
        return TIMS_testlog
    port = cfg['msr']['sanity_port']
    prefix = cfg['sanity']['household_prefix'] 
    headers = {
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
        'Accept': 'application/json',
        }  
    timeout = 5 
    any_host_pass = 0 
    for index, host in enumerate(hosts):
        url = protocol + "://" + host + ":" + str(port) + "/api/v1/endpoints"
        print "List endpoints from cluster via " + url
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
                    print "List endpoints from cluster: \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                    print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                any_host_pass = any_host_pass + 1
                printLog("List endpoints from cluster: \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)
                response = json.loads(r.content)
                for value in response['items']:  
                    endpont_name = value['metadata']['name']    
                    print "Name of the endpoint: ", endpont_name
    if  any_host_pass :
         msg = 'Testcase passed :List endpoints from cluster ran successfully.'
         print msg
         TIMS_testlog.append(0)
         TIMS_testlog.append(msg)
         return TIMS_testlog

    else:
         msg = 'Testcase failed :List endpoints from cluster was not successful.'
         print msg
         TIMS_testlog.append(1)
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
                                    
