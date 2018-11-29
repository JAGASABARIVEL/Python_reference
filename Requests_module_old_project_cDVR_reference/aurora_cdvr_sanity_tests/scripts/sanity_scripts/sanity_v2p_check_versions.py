#!/usr/bin/python

import os
import sys
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
##########################################################################
#   Check V2PC Version
##########################################################################

def doit(cfg,printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'Check V2PC Version'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    # set values based on config
    protocol = cfg['protocol']
    v2p_protocol = cfg['v2p']['protocol']
    token = cfg['v2p']['api_token']
    Authorization = 'Bearer cisco:' + token  
    v2p_masterNode = cfg['v2p']['masters']
    port = cfg['v2p']['mgmt_port']
    prefix = cfg['sanity']['household_prefix'] 
    headers = {
        'Authorization': Authorization
    }
    timeout = 2
    V2pc_check = 0
    message_list = []
    for index,v2pmasternode  in enumerate(v2p_masterNode):
        print "Checking  V2PC Version for: " , v2pmasternode
        householdid = prefix + str(index)
        url = v2p_protocol + "://" + v2pmasternode + ":" + str(port) + "/sm/v2/mgmtcontrol/buildversions"
        print "Check  V2PC Version via " + url
        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                message = "could not Check V2PC Version for v2p master node: " + v2pmasternode
                print message
                message_list.append(message) 
                print r.status_code
                print r.headers
                print r.content
            else:
                if r.content is None :
                    print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                    print "\nCheck V2PC Version = " + r.content
                    print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                else:
                    V2pc_check  = V2pc_check + 1
                    printLog("\nCheck V2PC Version = " + r.content,printflg)
                    message = "Checked v2pc version successfully for: " , v2pmasternode
                    message_list.append(message)
        else:
            message = "Error in getting responce, could not Check V2PC Version for v2p master node: " + v2pmasternode
            message_list.append(message)
    for item in message_list:
        print item
    if V2pc_check == len(v2p_masterNode):        
        print "\n\nTestcase Passed: Check V2PC Version ran succesfully"   
        TIMS_testlog.append(0)
        TIMS_testlog.append('Check V2PC Version ran succesfully')
        return TIMS_testlog
    else:
        print "\n\nTestcase Failed: Check V2PC Version was not successful"  
        TIMS_testlog.append(1)
        TIMS_testlog.append('Check V2PC Version was not successful.')
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

