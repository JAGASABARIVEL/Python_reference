#!/usr/bin/python
import json 
import os
import sys
from pprint import pprint
import calendar
import requests
import random
import time
import itertools
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *

##########################################################################
#   Pps Booking
##########################################################################
def doit(cfg,printflg=False):
    try :
        disable_warning()   #Method Called to suppress all warnings
        any_host_pass = 0
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        name = (__file__.split('/'))[-1]
        I = 'Core DVR Functionality'     #rally initiatives
        US = 'Pps Booking'
        TIMS_testlog = []
        TIMS_testlog = [name,I,US]
        print "Starting test " + test
        index = 0
        contentId_list  = []
        protocol = cfg['protocol']
        catalogueId = cfg['catalogueId']
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        region = cfg['region']
        cmdc_hosts = get_hosts_by_config_type(cfg,'cmdc',printflg) 
        pps_hosts = get_hosts_by_config_type(cfg,'pps',printflg)
        if cmdc_hosts == None or pps_hosts == None:
            msg = 'Testcase failed : unable to get host ip '
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        prefix = cfg['sanity']['household_prefix']
        cmdc_headers = {
            'Accept': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
                }
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
                   }
        throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
        if throttle_milliseconds < 1:
            throttle_milliseconds = 25
        timeout = 2
        result = "FAIL"
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts))  
        printLog("Final list :"+ str(hosts_list),printflg)
        for (cmdc_host,pps_host) in hosts_list :
            householdid = prefix + str(index)
            if (len(cmdc_host) > 1 and len(pps_host) > 1):
                time.sleep(throttle_milliseconds / 1000.0 )
            serviceid_responce= fetch_serviceIdbyregion(protocol,cmdc_host,cmdc_port,region,timeout)
            if serviceid_responce :
                serviceIdlist= get_serviceIdlist(serviceid_responce)
                gridResponce =  fetch_gridRequest(catalogueId,protocol,cmdc_host,cmdc_port,serviceIdlist,region,timeout,printflg=False)
                if gridResponce:
                    contentId_list = get_contentIdlist(gridResponce)
                    if not contentId_list:
                        print "contentId list could not be fetched for the given timeframe from the grid responce"
                        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                        grid_Response = json.dumps(json.loads(gridResponce.content),indent = 4, sort_keys=False)
                        print "Grid Response:\n" + str(grid_Response)
                        print "\n" + "#"*20 + " DEBUG ENDED "+ "#"*20+ "\n"
                    else:
                         random_contentId =  random.choice(contentId_list)
                         payload = """
                            {
                                "scheduleInstanceId" : "%s",
                                "checkConflicts" : false, 
                                "pvr":"nPVR"
                            } 
                              """ % (random_contentId)
                         result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,payload,random_contentId,timeout,printflg=False)
                         if result =="PASS":
                             print "PPS booking is successfull for content ID :",random_contentId
                             any_host_pass = any_host_pass + 1 
                         else:
                             print "PPS booking is not successfull for content ID :",random_contentId
                else:
                    print "Error in retrieving grid response for the region" 
            else:
                print "Error in retrieving Service id for the region" 
        if (any_host_pass > 0) :
            msg = 'Testcase passed : PPS booking is successful '
            print msg
            TIMS_testlog.append(0)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            msg = 'Testcase failed :PPS booking is not  successful '
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

