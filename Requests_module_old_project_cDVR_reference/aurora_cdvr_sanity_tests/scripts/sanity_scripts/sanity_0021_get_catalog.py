#!/usr/bin/python

import os
import sys
import time
import requests
import json
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
##########################################################################
#   Get Catalog
##########################################################################

def doit(cfg,printflg=False):
    try :
        disable_warning()   #Method Called to suppress all warnings
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        name = (__file__.split('/'))[-1]
        I = 'Core DVR Functionality'     #rally initiatives
        US = ' Get Catalog services'
        TIMS_testlog = []
        TIMS_testlog = [name,I,US]
        print "Starting test " + test
        # set values based on config
        protocol = cfg['protocol']
        hosts = get_hosts_by_config_type(cfg,'pps',printflg)
        if hosts == None :
            msg = 'Testcase failed :unable to get host ip'
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        port = cfg['pps']['port']
        prefix = cfg['sanity']['household_prefix'] 
        throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
        if throttle_milliseconds < 1:
            throttle_milliseconds = 25
        headers = {
              'Source-Type': 'WEB',
              'Source-ID': '127.0.0.1',
              'Accept': 'application/json',
           }
        timeout = 2
        any_host_pass = 0
        for index, host in enumerate(hosts):
            if index > 1:
                time.sleep(throttle_milliseconds / 1000.0 )
            householdid = prefix + str(index)
            url = protocol + "://" + host + ":" + str(port) + "/pps/households/" + householdid + "/catalog"
            print "Get Catalog via " + url
            r = sendURL ("get",url,timeout,headers)
            if r is not None :
                if ( r.status_code != 200):
                    print "Problem accessing: " + url
                    print r.status_code
                    print r.headers
                    print r.content
                else:
                    if r.content is not None:
                        any_host_pass = any_host_pass + 1
                        printLog("Catalog\n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg) 
                    else :
                          print "### DEBUG STARTED ### \n\n"
                          response = json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                          print "catalog response : \n\n"
                          print response
                          print "### DEBUG ENDED ### \n\n"
        if any_host_pass :
            msg = 'Testcase passed : service catalog is fetched successfully'
            print msg
            TIMS_testlog.append(0)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            msg = 'Testcase failed : service catalog is  not fetched successfully'
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog
    except:
          msg = "Testcase failed : Error Occurred in Script: " + PrintException(True)
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

