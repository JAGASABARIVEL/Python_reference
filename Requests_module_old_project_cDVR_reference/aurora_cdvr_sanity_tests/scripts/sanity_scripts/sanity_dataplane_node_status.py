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
##########################################################################
#   Get Node Status
##########################################################################
def doit(cfg,printflg=False):
    # announce
    disable_warning()   #Method Called to suppress all warnings
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = ' Get Node Status'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    print "Starting test " + test
    # set values based on config
    mos_host = cfg['mos']['v2url']
    msr_host = cfg['msr']['v2url']
    recording_api = cfg['recording_api']
    v2p_host=cfg['v2p']['masters']
    v2p_port=cfg['v2p']['api_port']
    protocal = "https"
    token_key  = cfg['v2p']['api_token']
    token  = "Bearer cisco:" + token_key 
    headers = {'Accept': 'application/json;charset=utf-8'}
    headers_v2p = {'Authorization':token}
    timeout = 5
    pass_counter = 0
    # get node status
    if recording_api == "v2p":
        for host in v2p_host:
            url = protocal + "://" + host + ":" + str(v2p_port) + "/v2/regions/region-0/nodestatuses"
            print "Get Node Status via ", url        
            r = sendURL ("get",url,timeout,headers_v2p)
            if r is not None :
                if ( r.status_code != 200):
                    print "Problem accessing: " + url
                    print r.status_code
                    print r.headers
                    print r.content
                    msg = "Testcase failed :Problem accessing url"
                    print msg
                    TIMS_testlog.append(1)
                    TIMS_testlog.append(msg)
                    return TIMS_testlog
                else:
                     if r.content is None :
                         print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                         print "Node Status \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                         print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                     status_val = json.loads(r.content)
                     for val in status_val:
                         printLog("Node Name:" + val["properties"]["nodeName"],printflg)
                         printLog("Node state is  " + val["properties"]["state"],printflg)
                     pass_counter = pass_counter + 1
        if pass_counter == len(v2p_host):
             TIMS_testlog.append(0)
             msg = 'Testcase passed:node status for all v2p host is successfully retrieved'
             print msg
             TIMS_testlog.append(msg)
             return TIMS_testlog
        else : 
             TIMS_testlog.append(1)
             msg = 'Testcase failed :error in retrieving node status for all v2p host'
             print msg
             TIMS_testlog.append(msg)
             return TIMS_testlog
    elif recording_api == "msr":
        url = msr_host + "/v2/regions/region-0/nodestatuses"
    else:
        url = mos_host + "/v2/regions/region-0/nodestatuses"
    print "Get Node Status via ", url        
    r = sendURL ("get",url,timeout,headers)
    if r is not None :
        if ( r.status_code != 200):
            print "Problem accessing: " + url
            print r.status_code
            print r.headers
            print r.content
            TIMS_testlog.append(1)
            msg = 'Testcase failed :Problem accessing url'
            print msg
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            printLog("Node Status \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)
            status_val = json.loads(r.content)
            if isinstance(status_val,list):
                for val in status_val:
                    printLog("Node Name:" + val["name"],printflg)
                    printLog("Node state is  " + val["properties"]["state"],printflg)
                    if val["properties"]["faultStatus"] == "None":
                        printLog("Node faultStatus is " + val["properties"]["faultStatus"],printflg)
                    else:
                        printLog ("******************************************************",printflg)
                        printLog("Node faultStatus is " + val["properties"]["faultStatus"],printflg)
                        printLog("Node faultDetail is " + val["properties"]["faultDetail"],printflg)
            msg= 'Testcase passed :Node Status is sccessfully retrieved '
            print msg
            TIMS_testlog.append(0)
            TIMS_testlog.append(msg)
            return TIMS_testlog
    msg = 'Testcase failed :Node Status is  not sccessfully retrieved'
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

