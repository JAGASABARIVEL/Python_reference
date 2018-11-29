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
    port = cfg['v2p']['mgmt_port']
    headers = {
        'Authorization': Authorization
    }
    timeout = 2
    verify_check = 0
    state_check = 0
    message_list = []
    for index,v2pmasternode  in enumerate(v2p_masterNode):
        print "Getting workflow app instances status for: " , v2pmasternode
        url = v2p_protocol + "://" + v2pmasternode + ":" + str(port) + "/sm/v2/type/appinstancestatuses"
        print "Get workflow app instances list via " + url
        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                message = "could not Get workflow app instances list for v2p master node: " + v2pmasternode
                print message
                message_list.append(message)
                print r.status_code
                print r.headers
                print r.content
            else:
                state_check = 0
                #printLog("\nworkflow app instances status = " + r.content,printflg)
                responce = json.loads(r.content)
                for values in responce:
                     if values['properties']['state'] == 'inservice':
                         pass
                     else:
                          print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                          print "\nworkflow app instances status = " + r.content
                          print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                          state_check = state_check + 1   
                          message = "App instance referance: state : "+ values['properties']['state'] + " for v2p masternode: "+ v2pmasternode
                          message_list.append(message)

                if state_check == 0 :
                    verify_check = verify_check + 1
                    message = "State is inservice for all id in v2p node: "+ v2pmasternode        
                    print message                    
                    message_list.append(message)
        else:
            message = "could not Get workflow app instances list for v2p master node: " + v2pmasternode
            print message
            message_list.append(message)
    print "\n\nApp instance status: "
    for item in message_list:
        print item
    if verify_check == len(v2p_masterNode):
          print "Testcase Passed: All the id present in app instance list are in 'inservice' state"  
          TIMS_testlog.append(0)
          TIMS_testlog.append('Get app instance status ran succesfully')
          return TIMS_testlog
    else:
         print "Testcase Failed:  All the id present in app instance list are not in 'inservice' state"
         TIMS_testlog.append(1)
         TIMS_testlog.append('Get app instance status was not successful')
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

