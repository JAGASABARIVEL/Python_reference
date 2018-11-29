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
#   DATAPLANE - Get Dynamic Channels
##########################################################################

def doit(cfg,printflg=False):
    disable_warning()   #Method Called to suppress all warnings
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = 'Get Dynamic Channels'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]
    if cfg['recording_api'] != 'msr':
        TIMS_testlog.append(2)
        msg = 'Testcase warning :This test not  valid for v2p.'
        TIMS_testlog.append(msg)
        print msg
        return TIMS_testlog
    print "Starting test " + test
    # set values based on config
    mos_host=cfg['mos']['v2url']
    msr_host=cfg['msr']['v2url']
    recordding_api =cfg['recording_api']
    mos_RecMgrName=cfg['mos']['active_name']
    msr_RecMgrName=cfg['msr']['active_name']
    headers = {
        'Accept': 'application/json',
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
    }
    timeout = 5
    IPaddress = None
    #Get Dynamic Channel lineups for the active IPAddress or else return 1 if there is any error
    if recordding_api == "msr":
        url = msr_host +"/v2/dynamicsources"
        RecMgrName = msr_RecMgrName
    else:
        url = mos_host +"/v2/dynamiclineups"
        RecMgrName = mos_RecMgrName
    print "Get dynamiclineups via ", url        
    r = sendURL ("get",url,timeout,headers)
    if r is not None :
        if ( r.status_code != 200):
            print "Problem accessing: " + url
            print r.status_code
            print r.headers
            print r.content
            msg = 'Testcase failed :Problem accessing url'
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            printLog("Data Plane - Get Dynamic Channel Lineups\n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)
            result=json.loads(r.content)
            for items in result:
                if items["name"]==mos_RecMgrName:
                    urlwithIPaddress=items["properties"]["interfaces"][0]["url"]
                    lastelement = urlwithIPaddress[-1]
                    if lastelement == '/' :
                         IPaddress=urlwithIPaddress[7:-1]
                    else:
                         IPaddress=urlwithIPaddress[7:]
                else:
                    if items["name"]==msr_RecMgrName:
                        urlwithIPaddress=items["properties"]["url"]
                        IPaddress=urlwithIPaddress[7:-5]
                if IPaddress :
                     if pingIPAddress(IPaddress,printflg)==True:
                          printLog("Ping to " + IPaddress + " is successful",printflg)
                          msg = 'Testcase passed :Ping to IPaddress is successful'
                          print msg 
                          TIMS_testlog.append(0)
                          TIMS_testlog.append(msg)
                          return TIMS_testlog
                     else:
                         print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                         print json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                         print "Ping to " + IPaddress + " is not successful"  
                         print "\n" + "#"*20 + " DEBUG ENDED "+ "#"*20+ "\n"
                         TIMS_testlog.append(1)
                         msg = 'Testcase failed :Ping to IPaddress is not successful'
                         print msg
                         TIMS_testlog.append(msg)
                         return TIMS_testlog
            print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
            print json.dumps(json.loads(r.content),indent = 4, sort_keys=False)        
            s = "Testcase failed : Record Manager Name " + RecMgrName + " defined in configuration file not found"     
            print s        
            print "\n" + "#"*20 + " DEBUG ENDED "+ "#"*20+ "\n"
            TIMS_testlog.append(1)
            TIMS_testlog.append(s)
            return TIMS_testlog
    else:
        msg=  "Testcase failed :Connection refused/No response from the server"
        TIMS_testlog.append(1)
        print msg
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

