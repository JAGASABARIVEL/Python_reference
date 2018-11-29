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
#   Get State Cache Endpoints
##########################################################################
def doit(cfg,printflg=False):
    # announce
    disable_warning()   #Method Called to suppress all warnings
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = 'Get State Cache Endpoints'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]
    print "Starting test " + test

    # set values based on config
    protocol = cfg['protocol']
    mos_host = cfg['mos']['v2url']
    msr_host = cfg['msr']['v2url']
    v2p_host=cfg['v2p']['masters']
    v2p_port=cfg['v2p']['mgmt_port']
    v2p_protocol = cfg['v2p']['protocol']
    recording_api = cfg['recording_api']
    headers = {
        'Accept': 'application/json',
        'charset': 'utf-8'
        }
    timeout = 5
    token_key  = cfg['v2p']['api_token']
    token  = "Bearer cisco:" + token_key
    headers = {'Accept': 'application/json;charset=utf-8'}
    headers_v2p = {'Authorization':token}
    if recording_api == "v2p":
         source_name = get_cache_endpoint(cfg,headers_v2p,["cisco-sce"])
         if source_name:
             pass_counter = 0
             for host in v2p_host :
                 url = v2p_protocol + "://" + host + ":" + str(v2p_port) + "/sm/v2/type/appinstancestatuses"
                 print "Get Capture Endpoints via " + url
                 r = sendURL ("get",url,timeout,headers)
                 if r is not None :
                     if ( r.status_code != 200):
                         print "Problem accessing: " + url
                         print r.status_code
                         print r.headers
                         print r.content
                         msg = 'Testcase failed :problem accessing url.'
                         print msg
                         TIMS_testlog.append(1)
                         TIMS_testlog.append(msg)
                         return TIMS_testlog
                     else:
                          #printLog("Captured Endpoints:\n"+json.dumps(json.loads(r.content),indent=4,sort_keys=False),printflg)
                          jsondata = json.loads(r.content)
                          end_point_check = 0
                          for end_point in source_name:
                              try:
                                  for val in jsondata :
                                      if str(val["name"]) == end_point :
                                          if str(val["properties"]["state"]) == "inservice":
                                              end_point_check = end_point_check + 1
                                          else:
                                              print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                                              print "Captured Endpoints:\n"+json.dumps(json.loads(r.content),indent=4,sort_keys=False)
                                              print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                              except:
                                      pass
                          if end_point_check == len(source_name):
                               pass_counter = pass_counter + 1
             if pass_counter == len(v2p_host):
                  TIMS_testlog.append(0)
                  message = "Testcase passed :cache_endpoint_list  is inservice state for all hosts"
                  print message
                  TIMS_testlog.append(message)
                  return TIMS_testlog
             else:
                  TIMS_testlog.append(1)
                  message = "Testcase failed :cache_endpoint_list is not inservice state for all hosts"
                  print message
                  TIMS_testlog.append(message)
                  return TIMS_testlog
         else:
              TIMS_testlog.append(1)
              message = "Testcase failed :error in retrieving cache end point "
              print message
              TIMS_testlog.append(message)
              return TIMS_testlog
    else:
        state_cache_endpoint_count = 0
        serviceinstances = Get_active_service_instances(cfg, "UMS", timeout)
        if len(serviceinstances) == 0:
            msg =  "Testcase failed :No Service Instances actively running on the Host"
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            printLog("List of Service Instances running for the host:\n" + str(serviceinstances),printflg) 
            for serviceinstance in serviceinstances:
                if recording_api == "msr":
                    url = msr_host + "/v2/serviceinstances/" + serviceinstance + "/captureendpoints" 
                else:
                    url = mos_host + "/v2/serviceinstances/" + serviceinstance + "/statecacheendpoints" 
                print "Get State Cache Endpoints via " + url
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
                        printLog("State Cache Endpoints:\n"+json.dumps(json.loads(r.content),indent=4,sort_keys=False),printflg)
                        jsondata = json.loads(r.text)
                        if len(jsondata) == 0:
                            state_cache_endpoint_count = state_cache_endpoint_count + 0
                            print "No State Cache Endpoints on that Service Instance %s" % serviceinstance
                        else:
                            state_cache_endpoint_count = state_cache_endpoint_count + 1
                            try:
                                for contents in jsondata:
                                    for keyproperties,valueproperties in contents['properties'].iteritems():
                                        if 'address' in keyproperties:
                                            vipaddress =  valueproperties['vip']
                                            printLog( "Ping the VIP " + vipaddress + " for the service instance : " + serviceinstance,printflg)
                                            #To check the Endpoint Active Status
                                            if pingIPAddress(vipaddress,printflg) == True:
                                                printLog('State Cache Endpoint {0} is ACTIVE'.format(vipaddress),printflg)
                                                printLog( "Pinging the VIP " + vipaddress + " for the service instance " + serviceinstance + " is successful ",printflg)
                                            else:
                                                print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                                                print json.dumps(json.loads(r.content),indent = 4,sort_keys=False)
                                                print  "PINGING the VIP " + vipaddress + " from the State Cache Endpoints is not successful"
                                                message =  "Testcase failed :PINGING the VIP from the State Cache Endpoints is not successful"
                                                print message 
                                                print "\n" + "#"*20 + " DEBUG ENDED "+ "#"*20+ "\n"
                                                TIMS_testlog.append(1)
                                                TIMS_testlog.append(message)
                                                return TIMS_testlog
                            except (KeyError, TypeError, ValueError, IndexError) as e:
                                print "Error Occurred: %s" % str(e)
                                msg = 'Testcase failed :Error Occurred in script'
                                print msg
                                TIMS_testlog.append(1)
                                TIMS_testlog.append(msg)
                                return TIMS_testlog
        #Return based on the count of State Cache endpoint. Return 1 if there is no Endpoint Cached for that capture cluster
        if state_cache_endpoint_count == 0:
            TIMS_testlog.append(1)
            msg = 'Testcase failed :State Cache Endpoints is not  retrieved successfully'
            print msg
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            msg = 'Testcase passed :State Cache Endpoints is retrieved successfully'
            print msg
            TIMS_testlog.append(0)
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

