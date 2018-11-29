#!/usr/bin/python

import os
import sys
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
##########################################################################
# Get channel linups
##########################################################################
def doit(cfg,printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'Get channel linups'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    # set values based on config
    channel_list = []
    protocol = cfg['protocol']
    v2p_protocol = cfg['v2p']['protocol']
    token = cfg['v2p']['api_token']
    Authorization = 'Bearer cisco:' + token  
    v2p_masterNode = cfg['v2p']['masters']
    port = cfg['v2p']['api_port']
    headers = {
        'Authorization': Authorization
         }
    timeout = 5
    for index,v2pmasternode  in enumerate(v2p_masterNode):
        print "Getting  channel linups for: " , v2pmasternode
        url = v2p_protocol + "://" + v2pmasternode + ":" + str(port) + "/v2/channellineups"
        print "Get channel linups via " + url
        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                message = "could not Get channel linups for v2p master node: " + v2pmasternode
                message_list.append(message) 
                print r.status_code
                print r.headers
                print r.content
            else:
                printLog("\nGet channel linups = " + r.content,printflg)
                message =  "Testcase passed: Get channel linups was successful"  
                print message
                TIMS_testlog.append(0)
                TIMS_testlog.append(message)
                return TIMS_testlog
        else:
            message = "Testcase Failed:could not Get channel linups for v2p master node: " + v2pmasternode
            print message  
            TIMS_testlog.append(1)
            TIMS_testlog.append("could not Get channel linups for v2p ")
            return TIMS_testlog
    else:
        message = "Testcase Failed: Get channel linups was not successful"  
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

