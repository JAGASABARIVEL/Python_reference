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
from L3commonFunctions import *
##########################################################################
#   Get Service Instances 
##########################################################################

def doit(cfg,printflg=False):
    # announce
    disable_warning()   #Method Called to suppress all warnings 
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = ' Get Service Instances'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]
    print "Starting test " + test
    ##########################################################################
    #   COS Authorization Issues in NFR
    ##########################################################################
    if True:
        message = "Testcase warning :Skipping all COS PAM Node API because of authorization issue; Tosin is looking into it"
        print message
        TIMS_testlog.append(2)
        TIMS_testlog.append(message)
        return TIMS_testlog
    # set values based on config
    mos_host=cfg['mos']['v2url']
    msr_host=cfg['msr']['v2url']
    v2p_host=cfg['v2p']['pam_node']
    v2p_port=cfg['v2p']['api_port']
    v2p_protocal = cfg['v2p']['protocol']
    recording_api=cfg['recording_api']
    headers = {
      'Content-Type': 'application/json',
      'charset': 'utf-8'
    }
    timeout = 5 
    if recording_api == "v2p" :
        url = v2p_protocal + "://" + v2p_host + ":" + str(v2p_port) + "/v2/serviceinstances"  
        print "Get Service Statuses via ", url
    elif recording_api == "msr":
        url = msr_host + "/v2/serviceinstances"  
        print "Get Service Statuses via ", url
    else:
        url = mos_host + "/v2/serviceinstances/"  
        print "Get Service Statuses via ", url

    # Get Service Instances List  
    instance_list = []       
    r = sendURL("get",url,timeout,headers)
    if r is not None :
        if ( r.status_code != 200):
            print "Problem accessing: " + url
            message = "Problem accessing url " 
            print r.status_code
            print r.headers
            print r.content
            TIMS_testlog.append(1)
            TIMS_testlog.append(message)
            return TIMS_testlog
        else:
            if r.content is None :
                print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                print "Get Service Statuses \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                msg = 'Testcase failed  : Error in retrieving the response o fthe URL '
                print msg
                TIMS_testlog.append(1)
                TIMS_testlog.append(msg)
                return TIMS_testlog
            printLog("Get Service Statuses \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)
            result= json.loads(r.content)
            for items in result:
                instance_list.append(items["name"])
            printLog ("List of Service Instances:\n" +str(instance_list),printflg)   
            msg = 'Testcase passed : Service Instances is successfully retrieved '
            print msg
            TIMS_testlog.append(0)
            TIMS_testlog.append(msg)
            return TIMS_testlog
    msg = 'Testcase failed : Service Instances not retrieved  successfully '
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

