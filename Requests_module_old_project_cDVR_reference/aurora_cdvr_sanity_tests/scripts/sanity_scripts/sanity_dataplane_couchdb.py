#!/usr/bin/python

import os
import sys
import time
import requests
import json
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
##########################################################################
#  Get CouchDB nodes
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
    US = 'Get CouchDB nodes'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]


    # set values based on config
    hosts = get_hosts_by_config_type(cfg,'rm',printflg)
    if hosts == None:
        msg  = 'Testcase failed :Host not present'
        print msg
        TIMS_testlog.append(1)
        TIMS_testlog.append(msg)
        return TIMS_testlog 
     
    protocol = cfg['protocol']
    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25
    headers = {'Accept': 'application/json;charset=utf-8'}
    timeout = 2
    any_host_pass = 0
    for index, host in enumerate(hosts):
        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )
        url = protocol + "://" + host + "/emdata/Couchbase/Nodes"
        print "Get CouchDB nodes via ", url        
        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
                msg = 'Testcase failed :problem accessing in url.'
                print msg 
                TIMS_testlog.append(1)
                TIMS_testlog.append(msg)
                return TIMS_testlog
            
            else:
                if r.content is None :
                    print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                    print "CouchDB nodes and status from Record Manager\n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                    print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                any_host_pass = any_host_pass + 1
                printLog("CouchDB nodes and status from Record Manager\n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)
                status_val = json.loads(r.content)
                if isinstance(status_val,list):
                    for val in status_val:
                        if val["NodeStatus"] == None :
                           val["NodeStatus"] = "null"
                        printLog("NodeIndex " + val["NodeIndex"],printflg)
                        printLog(" status is " + val["status"],printflg)
                        printLog(" NodeStatus is " +val["NodeStatus"] ,printflg)
    if any_host_pass:
        msg  = 'Testcase passed :Get CouchDB nodes ran successfully.'
        print msg
        TIMS_testlog.append(0)
        TIMS_testlog.append(msg)
        return TIMS_testlog

    else:
        msg = 'Testcase failed :could not get CouchDB nodes.'
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



