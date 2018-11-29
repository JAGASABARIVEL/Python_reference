#!/usr/bin/python
import json
import os
import sys
from pprint import pprint
import time
import random
import requests
import calendar
import itertools
import mypaths
from readYamlConfig import readYAMLConfigs
from getCatalogServices import getCdvrServiceIds
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
##########################################################################
#   Get Events based on content Id 
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
    US = 'Get Events based on content Id'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    # set values based on config
    protocol = cfg['protocol']
    cmdc_hosts = get_hosts_by_config_type(cfg,'cmdc',printflg)
    hc_hosts = get_hosts_by_config_type(cfg,'hc',printflg)
    cmdc_port = cfg['cmdc']['port']
    region = cfg['region']
    catalogueId = cfg['catalogueId']
    hc_port = cfg['hc']['port']
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
    hosts_list = list(itertools.product(cmdc_hosts,hc_hosts))
    printLog("Final list :"+ str(hosts_list),printflg)
    for (cmdc_host,hc_host) in hosts_list :
        if (len(cmdc_hosts) > 1 and len(hc_hosts) > 1):
            time.sleep(throttle_milliseconds / 1000.0 )
        serviceid_responce= fetch_serviceIdbyregion(protocol,cmdc_host,cmdc_port,region,timeout)
        if serviceid_responce :
            serviceIdlist=get_serviceIdlist(serviceid_responce)
            if serviceIdlist :
                gridResponce =  fetch_gridRequest(catalogueId,protocol,cmdc_host,cmdc_port,serviceIdlist,region,timeout,printflg=False)
                if gridResponce:
                    contentId_list = get_contentIdlist(gridResponce)
                    if not  contentId_list :
                        print "contentId list could not be fetched"
                    else:
                        printLog(contentId_list,printflg)
                        random_contentId =  random.choice(contentId_list)
                        printLog("list of contentIds for 1 hr duration",printflg)
                        url =protocol +"://" + hc_host + ":" + str(hc_port) + "/mdp/content?filter:" + "contentId"  + "=" + random_contentId + "&pset=mdp:no-presentation&sourceType=uhe&targetType=uhe" 
                        print "Get all event via " + url
                        r = sendURL ("get",url,timeout,headers) 
                        if r is not None :
                            if ( r.status_code != 200):
                                 print "Problem accessing: " + url
                                 print r.status_code
                                 print r.headers
                                 print r.content
                            else:
                                if r.content is None:
                                    print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                                    print "\n  Detail of the event for contentId  : " + random_contentId +"\n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                                    print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                                else:
                                     any_host_pass = any_host_pass + 1
                                     printLog("\n  Detail of the event for contentId  : " + random_contentId +"\n" + json.dumps(json.loads(r.content),indent = 4, sort_keys=False),printflg)
                else:
                     print "unable to get the grid response "
            else:
                print "unable to get the service list"
        else:
            print "unable to get the service response"
    if any_host_pass :
         msg = 'Testcase passed :Get Events based on content Id ran successfully.'
         print msg
         TIMS_testlog.append(0)
         TIMS_testlog.append(msg)
         return TIMS_testlog

    else:
         msg = 'Testcase failed :Get Events based on content Id was not successful'
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

