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
#   Get Capture Endpoints
##########################################################################
def doit(cfg,printflg=False):
    # announce
    disable_warning()   #Method Called to suppress all warnings
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'Get Capture Endpoints'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    # set values based on config
    protocol = cfg['protocol']
    mos_url = cfg['mos']['v2url']
    msr_url = cfg['msr']['v2url']
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
         source_name = get_cache_endpoint(cfg,headers_v2p,["cisco-vmr"])
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
                         msg = 'Testcase failed : problem accessing url.'
                         print msg 
                         TIMS_testlog.append(1)
                         TIMS_testlog.append(msg)
                         return TIMS_testlog
                     else:
                          #printLog("Captured Endpoints:\n"+json.dumps(json.loads(r.content),indent=4,sort_keys=False),printflg)
                          jsondata = json.loads(r.content)
                          for val in jsondata : 
                              try :
                                  if str(val["name"]) == source_name[0] :
                                      if str(val["properties"]["state"]) == "inservice":
                                           pass_counter = pass_counter + 1
                                      else:
                                          print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                                          print "Captured Endpoints:\n"+json.dumps(json.loads(r.content),indent=4,sort_keys=False)
                                          print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                              except:
                                    pass
             if pass_counter == len(v2p_host):
                   TIMS_testlog.append(0)
                   print  "Testcase passed: " , source_name ,  " end point is inservice state for all hosts"
                   message = "Testcase passed:  end point is inservice state for all hosts"
                   TIMS_testlog.append(message)
                   return TIMS_testlog
             else:
                   TIMS_testlog.append(1)
                   print "Testcase failed: ", source_name , " end point is not inservice state for all hosts"
                   message ="Testcase failed:  end point is not inservice state for all hosts"
                   TIMS_testlog.append(message)
                   return TIMS_testlog
         else:
              TIMS_testlog.append(1)
              message = "TEstcase failed :unable to receive the cache end point "
              print message
              TIMS_testlog.append(message)
              return TIMS_testlog
    else: 
        capture_endpoint_count = 0
        serviceinstances = Get_active_service_instances(cfg, "UMS", timeout)
        if len(serviceinstances) == 0:
            print "No Service Instances actively running on the Host"
            TIMS_testlog.append(1)
            msg  = 'TEstcase failed :No Service Instances actively running on the Host.'
            print msg
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            printLog("List of Service Instances running for the Host:\n" + str(serviceinstances) ,printflg)
            for serviceinstance in serviceinstances:
                if recording_api == "msr" :
                    url = msr_url + "/v2/serviceinstances/" + serviceinstance + "/captureendpoints" 
                else:
                    url = mos_url + "/v2/serviceinstances/" + serviceinstance + "/captureendpoints" 
                print "Get Capture Endpoints via " + url
                r = sendURL ("get",url,timeout,headers)
                if r is not None :
                    if ( r.status_code != 200):
                        print "Problem accessing: " + url
                        print r.status_code
                        print r.headers
                        print r.content
                        msg = 'Testcase failed :problem accessing url.'
                        TIMS_testlog.append(1)
                        TIMS_testlog.append(msg)
                        return TIMS_testlog
                    else:
                        printLog("Captured Endpoints:\n"+json.dumps(json.loads(r.content),indent=4,sort_keys=False),printflg)
                        jsondata = json.loads(r.text)
                        if len(jsondata) == 0:
                            capture_endpoint_count = capture_endpoint_count + 0
                            print "No Endpoints captured for the service instance %s " % serviceinstance
                        else:
                            capture_endpoint_count = capture_endpoint_count + 1
                            try:
                                for contents in jsondata:
                                    for keyproperties,valueproperties in contents['properties'].iteritems():
                                        if 'address' in keyproperties:
                                            vipaddress =  valueproperties['vip']
                                            printLog( "Ping the VIP " + vipaddress + " for the service instance : " + serviceinstance,printflg)
                                            #To check the Endpoint Active Status
                                            if pingIPAddress(vipaddress,printflg) == True:
                                                printLog('Captured Endpoint {0} is ACTIVE'.format(vipaddress),printflg)
                                                printLog( "Pinging the VIP " + vipaddress + "for the service instance " + serviceinstance  + " is successful",printflg)
                                            else:
                                                print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                                                print json.dumps(json.loads(r.content),indent = 4,sort_keys=False)
                                                print "PINGING the VIP " + vipaddress + " from the Captured Endpoints is not successful"
                                                print "\n" + "#"*20 + " DEBUG ENDED "+ "#"*20+ "\n"
                                                TIMS_testlog.append(1)
                                                msg = 'Testcase failed : pinging from the Captured Endpoints is not successful'
                                                print msg
                                                TIMS_testlog.append(msg)
                                                return TIMS_testlog
                            except (KeyError, TypeError, ValueError, IndexError) as e:
                                print "Error Occurred: %s" % str(e)
                                TIMS_testlog.append(1)
                                msg = 'Testcase failed :Error occurred: exception'
                                print msg
                                TIMS_testlog.append(msg)
                                return TIMS_testlog
        #Return based on the count of captured endpoint. Return 1 if there is no Endpoint captured for the service instance
        if capture_endpoint_count == 0:
            TIMS_testlog.append(1)
            msg = 'Testcase failed :Get Capture end points not successful.'
            print msg
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            msg = 'Testcase passed :Get Capture end points ran successfully.'
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

