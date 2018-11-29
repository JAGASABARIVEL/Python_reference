#!/usr/bin/python

import os
import sys
from pprint import pprint
import time
import requests
import calendar
import json
import mypaths
import itertools
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L3commonFunctions import *
from genChannelLineup import *

##########################################################################
#  Get Copy Type for a particular event
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
    US = 'Get all events in window'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]

    # set values based on config
    protocol = cfg['protocol']
    hosts = get_hosts_by_config_type(cfg,'ipom',printflg)
    if hosts == None :
        msg = 'Testcase failed :Host not found'
        print msg
        TIMS_testlog.append(1)
        TIMS_testlog.append(msg)
        return TIMS_testlog
    serviceidlist = []
    port = cfg['ipom']['port']
    upm_port = cfg['upm']['port']
    pps_port = cfg['pps']['port']
    port_cmdc = cfg['cmdc']['port']
    region = cfg['region']
    catalogueId = cfg['catalogueId']
    available_channels = cfg['catchup-restart-channels']
    channel_1 = cfg['test_channels'][available_channels[0]]['ServiceId']
    serviceidlist.append(unicode(channel_1))
    pps_hosts = [cfg['pps']['host']]
    cmdc_hosts = [cfg['cmdc']['host']]

    prefix = cfg['corner']['household_prefix']
    pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    hosts_list = list(itertools.product(cmdc_hosts, pps_hosts))
    printLog("Final list :" + str(hosts_list), printflg)
    householdlimit = cfg['corner']['households_needed']
    index = random.randint(0, householdlimit - 1)
    householdid = prefix + str(index)
    print "\n\n### STEP1: Ingest Event of n minutes(with posttime of n minutes) ###"
    ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
    seconds = 1
    post_time = time.time()
    ci_host = cfg['ci']['host']
    ci_port = cfg['ci']['port']
    twominuteprogramlength = cfg['test_channels']['mediumProgramLength'] + 190
    title = 'ipomsanity' + str(random.randint(1, 554))
    ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
    ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
    channel = ChannelLineup(BoundaryInMinutes=0)
    channel.add_to_lineup(serviceId=channel_1, timeSlotLengthMinutes=twominuteprogramlength, timeSlotCount=1, programIDPrefix=title)
    channel.postXmlData(ci_host, ci_port, startTime=post_time)
    channel.writeXmlFiles(startTime=post_time)
    print channel
    length = channel.getTotalLength()

    if throttle_milliseconds < 1:
      throttle_milliseconds = 25
    headers = {
     'Accept': 'application/json'
      }
    timeout = 2
    for index, host in enumerate(hosts):
        for (cmdc_host, pps_host) in hosts_list:
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)
	    try:
               grid_response = fetch_gridRequest(catalogueId, protocol, cmdc_host, port_cmdc, serviceidlist, region, timeout, printflg=False)
               grid_content = json.loads(grid_response.content)
               assert grid_response, " Testcase Failed : Unable to Fetch Grid Response"
               contentId_dict = get_currentandfuture_contentIddict(grid_response, title, ['title'])
               assert contentId_dict," Testcase Failed : Unable to Form ContentId dictionary from the Grid Response"
               event_contentId_list = sorted(contentId_dict.items(), key=lambda x: x[1])
               assert event_contentId_list, " Testcase Failed : Unable to form ContentId list from ContentId dictionary"
               print "contentID list===", event_contentId_list
               startTime = event_contentId_list[0][1][0]
               endTime = event_contentId_list[0][1][1]
               scheduleid = (str(event_contentId_list[0][0]).split('~'))[0]
               conten = next(iter(grid_content))
               for it in grid_content[conten]:
                   serviceEqKey = it['serviceEquivalenceKey']
	       print "### Passing StartTime, EndTime, ServiceEquivalenceKey, ID to iPOM for finding CopyType of the event #### \n"
               copyType_resp = get_copyType(protocol, host,port, scheduleid, serviceEqKey, startTime, endTime, timeout=2)
               resp = json.loads(copyType_resp.content)
               event_copyType = resp[0]['policy']['copyType']
               print "CopyType of the event with contentID %s is" % scheduleid, event_copyType
               assert event_copyType is not None, "Testcase Failed: copyType is empty" 
	       msg = "Testcase Passed: CopyType is found for contentID"
               print msg
               TIMS_testlog.append(0)
               TIMS_testlog.append(msg)
               return TIMS_testlog

            except AssertionError as ae:
               msg = 'Testcase failed :Get all events in window was not successful.'
               print msg
               debug_print_log(pps_port, protocol, pps_host, householdid, timeout)
               TIMS_testlog.append(1)
               TIMS_testlog.append(msg)
               return TIMS_testlog
            
            except Exception as e:
               msg = 'Testcase failed :Get all events in window was not successful.'
               print msg
               debug_print_log(pps_port, protocol, pps_host, householdid, timeout)
               TIMS_testlog.append(1)
               TIMS_testlog.append(msg)
               return TIMS_testlog
            finally:
               print "Reverting back household to original state"
               cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
      
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
