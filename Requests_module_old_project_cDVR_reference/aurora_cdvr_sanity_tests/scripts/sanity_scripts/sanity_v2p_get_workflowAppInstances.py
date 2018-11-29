#!/usr/bin/python

import os
import sys
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
##########################################################################
#   Get workflow app instances status
##########################################################################

def doit(cfg,printflg=False):
  try:
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'Get workflow app instances status'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    # set values based on config
    protocol = cfg['protocol']
    v2p_protocol = cfg['v2p']['protocol']
    token = cfg['v2p']['api_token']
    Authorization = 'Bearer cisco:' + token  
    v2p_masterNode = cfg['v2p']['masters']
    if v2p_masterNode == None :
        TIMS_testlog.append(1)
        TIMS_testlog.append('v2p_masterNode not found')
        return TIMS_testlog
    port = cfg['v2p']['mgmt_port']
    prefix = cfg['sanity']['household_prefix'] 
    headers = {
        'Authorization': Authorization
    }
    timeout = 2
    verify_check = 0
    App_instance_list = []
    for index,v2pmasternode  in enumerate(v2p_masterNode):
        print "Getting workflow app instances status for: " , v2pmasternode
        householdid = prefix + str(index)
        url = v2p_protocol + "://" + v2pmasternode + ":" + str(port) + "/sm/v2/type/mediaflowinstances?view=combined" 
        print "Get workflow app instances status via " + url
        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                message = "could not Get workflow app instances list for v2p master node: " + v2pmasternode
                print message
                App_instance_list.append(message)
                print r.status_code
                print r.headers
                print r.content
            else:
                state_check_counter = 0
                printLog("\nworkflow app instances status = " + r.content,printflg)
                responce = json.loads(r.content)
                for value in responce:
                     if value['properties']['systems']['state'] == "enable":
                        pass
                     else: 
                          print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                          print "\nworkflow app instances status = " + r.content
                          print "\n" + "#"*20 + " DEBUG ENDED "+ "#"*20+ "\n"
                          state_check_counter = state_check_counter + 1
                          message = "State: " + value['properties']['systems']['state'] + " for id: " + value['id']
                          App_instance_list.append(message) 
                if state_check_counter == 0:
                     verify_check = verify_check + 1  
                     message = "App instance verified successfully for v2p master node: " + v2pmasternode 
                     print message
                     App_instance_list.append(message)
        else:
            message = "could not Get workflow app instances list for v2p master node: " + v2pmasternode
            print message
            App_instance_list.append(message)
    for val in App_instance_list:
        print val
    if verify_check == len(v2p_masterNode):
        print "\nTestcase Passed: succesfully got app instance list for all v2p masternodes and all the worflow state are inservice" 
        TIMS_testlog.append(0)
        TIMS_testlog.append('Get workflow app instances list ran succesfully')
        return TIMS_testlog
    else:
        print "\nTestcase Failed: could not get app instance list for all v2p masternodes"
        TIMS_testlog.append(1)
        TIMS_testlog.append('Get workflow app instances list was not successful')
        return TIMS_testlog 
  except:
    message = "Error occured in script" + PrintException(True)
    print message
    TIMS_testlog.append(1)
    TIMS_testlog.append(message)
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

