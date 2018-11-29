#!/usr/bin/python

import os
import sys
import time
import requests
import json
import ast
import random
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
#from requests.auth import HTTPDigestAuth
##########################################################################
#   Get NFR container list
##########################################################################

def doit(cfg,printflg=False):
    disable_warning()   #Method Called to suppress all warnings    
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = 'Get NFR container list'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]
    print "Starting test " + test
    recording_api = cfg['recording_api']
    if recording_api != 'mos':
        TIMS_testlog.append(2)
        msg = 'Testcase warning : Test bypassed since for MOS'
        print msg
        TIMS_testlog.append(msg)
        return TIMS_testlog
    #set values based on config
    timeout=2
    hosts=cfg['cos']['urls']
    print hosts
    any_host_pass = 0
    for host_ip in hosts :
        token = get_cos_NFR_token(cfg,timeout,host_ip)
        if token :
            auth_token = token.headers['x-auth-token']
            Storage_Url = token.headers['x-storage-url']
            path = Storage_Url.split('/')
            stored_path = path[-1]
            printLog(json.dumps(json.loads(json.dumps( dict(token.headers) )),indent = 4, sort_keys=False),printflg)
            headers = {
                'x-auth-token':auth_token
               }
            url = host_ip + "/v1/" + stored_path 
            print "Get NFR container list via ", url        
            r = sendURL("get",url,timeout,headers)
            if r is not None :
                if ( r.status_code != 200):
                    print "Problem accessing: " + url
                    print r.status_code
                    print r.headers
                    print r.content
                else:
                    if r.content is not None:
                        printLog("Get NFR container list \n" + r.content,printflg)
                        any_host_pass = any_host_pass + 1
                    else:
                        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                        print "Get NFR container list \n" + r.content
                        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "Error in retreiving the token for host ip" , host_ip
    if any_host_pass :
        msg = 'Testcase passed : Get  NFR container list  is successfully retrieved'
        print msg
        TIMS_testlog.append(0)
        TIMS_testlog.append(msg)
        return TIMS_testlog
    else :
        msg = 'Testcase failed :Get  NFR container list  is not  successfully retrieved'
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


