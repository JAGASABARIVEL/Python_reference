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
#  Check the condition of each component 
##########################################################################

def doit(cfg,printflg=False):
    # announce 
    disable_warning()   #Method Called to suppress all warnings
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = 'Check the condition of each component'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]
    if cfg['recording_api'] != 'msr':
        TIMS_testlog.append(2)
        msg = 'Testcase warning : This test only valid for msr.'
        TIMS_testlog.append(msg)
        print msg
        return TIMS_testlog

    print "Starting test " + test
    headers = {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache'
    }
    timeout = 5 
    protocol = cfg['protocol']
    hosts = get_hosts_by_config_type(cfg,'msr',printflg)
    if hosts == None :
        msg = 'Testcase failed : Host not found.'
        print msg
        TIMS_testlog.append(1)
        TIMS_testlog.append(msg)
        return TIMS_testlog

    port =cfg['msr']['sanity_port'] 
    for index, host in enumerate(hosts):
        url = protocol + "://" + host + ":" + str(port) + "/api/v1/componentstatuses"
        print "List all the components via url :",url
        r = sendURL("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                message = "Problem accessing: " + url
                print message
                print r.status_code
                print r.headers
                print r.content
                TIMS_testlog.append(1)
                TIMS_testlog.append(message)
                return TIMS_testlog
            else:
                if r.content == "[]":
                     print "### DEBUG STARTED ### \n\n"
                     response = json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                     print "Get list of all the components: \n"
                     print response
                     print "### DEBUG ENDED ### \n\n"
                else:
                    printLog("Get list of all the components \n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)
                    result = json.loads(r.content)
                    for condition in result['items']:
                        print "Component_name : ",condition['metadata']['name']
                        print "Type : ",condition['conditions'][0]['type']
                        print "status :",condition['conditions'][0]['status']
                    msg = 'Testcase passed : Condition of each component is successfully retrieved '
                    print msg
                    TIMS_testlog.append(0)
                    TIMS_testlog.append(msg)
                    return TIMS_testlog     
        msg = 'Testcase failed : Condition of each component is not retrieved  successfully '
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

