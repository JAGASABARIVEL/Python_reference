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
    any_host_pass = 0
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives
    US = 'Pps Booking'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]
    if cfg['recording_api'] != 'msr':
        TIMS_testlog.append(2)
        msg = 'This test only valid for msr.'
        TIMS_testlog.append(msg)
        print msg
        return TIMS_testlog

    print "Starting test " + test
    index = 0
    protocol = cfg['protocol']
    catalogueId = cfg['catalogueId']
    cmdc_port = cfg['cmdc']['port']
    pps_port = cfg['pps']['port']
    region = cfg['region']
    cmdc_hosts = get_hosts_by_config_type(cfg,'cmdc',printflg) 
    pps_hosts = get_hosts_by_config_type(cfg,'pps',printflg)
    if cmdc_hosts == None or pps_hosts == None:
        TIMS_testlog.append(1)
        TIMS_testlog.append('unable to get host ip ')
        return TIMS_testlog
    host = cfg['msr']['host']
    if host == None :
        TIMS_testlog.append(1)
        TIMS_testlog.append('Host not found.')
        return TIMS_testlog

    port = cfg['msr']['functional_port']
    prefix = cfg['sanity']['household_prefix']
    headers = {
      'Pragma': 'no-cache',
      'Origin': 'http://rio.msr-scale.vdc7.vcte.com:9110',
      'Accept': 'application/json, text/plain, */*',
      'Cache-Control': 'no-cache',
      'Authorization': 'Basic bmdpbng6bmdpbng=',
      'Connection': 'keep-alive'
    }
    timeout = 10
    any_pass_check = 0  
    hosts_list = list(itertools.product(cmdc_hosts,pps_hosts))  
    printLog("Final list :"+ str(hosts_list),printflg)
    for (cmdc_host,pps_host) in hosts_list :
        serviceid_responce= fetch_serviceIdbyregion(protocol,cmdc_host,cmdc_port,region,timeout)
        serviceIdlist=get_serviceIdlist(serviceid_responce)
        householdid = prefix + str(index)
        serviceID = random.choice(serviceIdlist)  
        print serviceIdlist
        url = protocol + "://" + host + ":" + str(port) + "/api/streams/id/" + serviceID 
        print "List All streams ", url
        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
            else:
                any_host_pass = any_host_pass + 1
                result=json.loads(r.content)
                for val in result:
                   url = val['URL']
                   print "List All streams ", url
                   r = sendURL ("get",url,timeout,headers)
                   if r is not None :
                       if ( r.status_code != 200):
                           print "Problem accessing: " + url
                           print r.status_code
                           print r.headers
                           print r.content
                       else:
                           print "successful ping to url"
                           print r.content
                           any_pass_check = any_pass_check + 1
    if any_pass_check :
         TIMS_testlog.append(0)
         TIMS_testlog.append('get stream by stream ID is successful ')
         return TIMS_testlog
    else :
         TIMS_testlog.append(1)
         TIMS_testlog.append('get stream by stream ID is not successful  ')
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

