#!/usr/bin/python

import os
import sys
import time
import requests
import json
import ast
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *

##########################################################################
#   Get MOS recorder
##########################################################################

def doit(cfg,printflg=False):
    disable_warning()   #Method Called to suppress all warnings    
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = ' Get MOS recorder'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    print "Starting test " + test
    recording_api = cfg['recording_api']
    if recording_api != 'mos':
        TIMS_testlog.append(2)
        msg = 'Testcase warning :Test bypassed since for MOS'
        print msg
        TIMS_testlog.append(msg)
        return TIMS_testlog
    # set values based on config
    hosts = get_hosts_by_config_type(cfg,'rm',printflg)
    print hosts
    if hosts == None:
        msg = 'Testcase failed :unable to get the host ip'
        print msg
        TIMS_testlog.append(1)
        TIMS_testlog.append(msg)
        return TIMS_testlog
    protocol = cfg['protocol']
    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25
    headers = {
               'Content-Type': 'application/json; charset=utf-8',
             }
    timeout=5
    any_host_pass = 0
    for index, host in enumerate(hosts):
        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )
        url = protocol +"://" + host + "/emdata/MosRecorder" 
        print "Get MOS recorder via ", url        
        r = sendURL("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
                msg= 'Testcase failed :Problem accessing url'
                print msg
                TIMS_testlog.append(1)
                TIMS_testlog.append(msg)
                return TIMS_testlog
            else:
                if r.content is None : 
                    print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                    print "Get MOS recorder \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                    print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                any_host_pass = any_host_pass + 1
                printLog("Get MOS recorder \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)
    if any_host_pass:
        msg = 'Testcase passed :MOS recorder is successfully retrieved'
        print msg
        TIMS_testlog.append(0)
        TIMS_testlog.append(msg)
        return TIMS_testlog
    else:
        msg = 'Testcase failed :MOS recorder is  not successfully retrieved '
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

