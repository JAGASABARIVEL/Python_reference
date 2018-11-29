#!/usr/bin/python

import os
import sys
import time
import pprint
import requests
import json
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L3commonFunctions import *
##########################################################################
#   Get cos NFR tokens 
##########################################################################

def doit(cfg,printflg=False):
    # announce
    disable_warning()   #Method Called to suppress all warnings
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = ' Get cos NFR tokens'
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
    hosts=cfg['cos']['urls']
    timeout = 2
    any_host_pass = 0
    for host_ip in hosts:
        NFR_token  = get_cos_NFR_token (cfg,timeout,host_ip)
        if NFR_token is not None :
            printLog(json.dumps(json.loads(json.dumps( dict(NFR_token.headers) )),indent = 4, sort_keys=False),printflg)
            any_host_pass = any_host_pass + 1 
    if any_host_pass :
        msg = 'Testcase passed :Get cos NFR tokens is successfully retrieved'
        print msg
        TIMS_testlog.append(0)
        TIMS_testlog.append(msg)
        return TIMS_testlog
    else:
        msg = 'Testcase failed :Get cos NFR tokens is not retrieved  successfully '
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

