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
# List all objects from COS 
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
    US = 'List all objects from COS'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    ########################   W A R N I N G   ###############################
    # ken bypassed until rewritten to use correct pam api
    #
    print "Bypassed since api used is incorrect"
    TIMS_testlog.append(2)
    TIMS_testlog.append('bypassed')
    return TIMS_testlog
    ########################   W A R N I N G   ###############################

    # set values based on config
    hosts = cfg['cos']['urls']
    print hosts
    if hosts == None :
        TIMS_testlog.append(1)
        TIMS_testlog.append('Host not found')
        return TIMS_testlog
    headers = {
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
        'Accept': 'application/json',
        }  
    timeout = 10 
    any_host_pass = 0 
    for index, host in enumerate(hosts):
        url =  host + "/rio"
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
                    print "List all objects from COS: \n" + r.content
                    print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                any_host_pass = any_host_pass + 1
                printLog("List all objects from COS: \n" + r.content, printflg)   

    if  any_host_pass == len(hosts):
         msg = 'Testcase passed :List all objects from COS ran succesfully'
         print msg
         TIMS_testlog.append(0)
         TIMS_testlog.append(msg)
         return TIMS_testlog

    else:
         msg = 'Testcase failed :List all objects from COS was not successful.'
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
                                    
