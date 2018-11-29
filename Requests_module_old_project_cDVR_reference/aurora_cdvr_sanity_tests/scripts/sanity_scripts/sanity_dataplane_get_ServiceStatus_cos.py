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
#   Get Service Statuses COS
##########################################################################

def doit(cfg,printflg=False):
    # announce
    disable_warning()   #Method Called to suppress all warnings
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = ' Get Service Statuses COS'
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
    recording_api=cfg['recording_api']
    v2p_host=cfg['v2p']['pam_node']
    v2p_port=cfg['v2p']['api_port']
    v2p_protocol = cfg['v2p']['protocol']
    headers = {
      'Content-Type': 'application/json',
      'charset': 'utf-8'
    }
    # Get Service State for the COS Service
    service = 'COS'
    timeout=5
    instance = Get_all_service_instances(cfg,service,timeout)
    any_service_found = 0
    if instance :
        printLog ("\nList of cos:"+str(instance),printflg)
        for i in instance :
            printLog ("Status for: "+str(i),printflg)
            if recording_api == "v2p" :
                url = v2p_protocol + "://" + v2p_host + ":" + str(v2p_port) + "/v2/serviceinstances/" + i
            elif recording_api == "msr":
                url = msr_host + "/v2/serviceinstances/" + i 
            else:
                url = mos_host + "/v2/serviceinstances/" + i 
            print "Get Service Statuses via ", url        
            r = sendURL("get",url,timeout,headers)
            if r is not None :
                if ( r.status_code != 200):
                    print "Problem accessing: " + url
                    print r.status_code
                    print r.headers
                    print r.content
                else:
                    if r.content is None:
                        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                        print "Get service instance : \n" + r.content
                        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                    result=json.loads(r.content)
                    if isinstance(result,dict):
                        printLog ("SERVICE NAME: "+ result["properties"]["title"],printflg)
                        printLog ("STATUS: "+ result["properties"]["state"]+ "\n",printflg)
                        any_service_found = any_service_found + 1
            else:
                 print "content details could not be fetched"
    else :
          print "service instances could not be fetched "
    if any_service_found :
         msg = 'Testcase passed :service instances fetched successfully '
         print msg
         TIMS_testlog.append(0)
         TIMS_testlog.append(msg)
         return TIMS_testlog
    else :
         msg = 'TEstcase failed :content details could not be fetched '
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

