#!/usr/bin/python
import json 
import os
import sys
from pprint import pprint
import time
import requests
import random
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
##########################################################################
#   GET Service Offer List
##########################################################################

def doit(cfg,printflg=False):
    disable_warning()   #Method Called to suppress all warnings
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'GET Service Offer List'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    # set values based on config
    caSystemId = str(cfg['caSystemId'])
    catalogueId = str(cfg['catalogueId'])
    protocol = cfg['protocol']
    cmdc_host = get_hosts_by_config_type(cfg,'cmdc',printflg)
    region = cfg['region']  
    port = cfg['cmdc']['port']
    prefix = cfg['sanity']['household_prefix']
    enabledServices = '"{0}"'.format('", "'.join(cfg['enabledServices']))
    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
      throttle_milliseconds = 25
    headers = {
      'Accept': 'application/json',
      'Source-Type': 'WEB',
      'Source-ID': '127.0.0.1',
    }
    timeout = 2
    any_host_pass = 0
    for index, host in enumerate(cmdc_host):
      if index > 1:
        time.sleep(throttle_milliseconds / 1000.0 )
      householdid = prefix + str(index)
      deviceid = householdid + 'd'
      serviceid_responce= fetch_serviceIdbyregion(protocol,host,port,region,timeout)
      serviceids = get_serviceIdlist(serviceid_responce)

      if not serviceids:
           print " serviceids list not present "
      else :
           channelId = random.choice(serviceids) 
           print channelId
           url = protocol + "://" + host + ":" + str(port) + "/cmdc/service/" + channelId + "/offers?catalogueId=" + catalogueId + "&caSystemId=" + caSystemId + "&count=255"
           print "Offer List for channel Id %s fetched via %s"%(channelId,url)
           r = sendURL ("get",url,timeout,headers)
           if r is not None :
              if ( r.status_code != 200):
                   print "Problem accessing: " + url
                   print r.status_code
                   print r.headers
                   print r.content
              else:
                   if r.content is None :
                       print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                       print "Offer List for channel Id" + channelId + json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                       print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                   any_host_pass = any_host_pass + 1
                   printLog("Offer List for channel Id" + channelId + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)

    if any_host_pass :
         msg = 'Testcase passed :GET Service Offer List ran successfully.'
         print msg
         TIMS_testlog.append(0)
         TIMS_testlog.append(msg)
         return TIMS_testlog

    else:
         msg = 'Testcase failed :GET Service Offer List was not successful.'
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

