#!/usr/bin/python

import os
import sys
import json
from pprint import pprint
import time
import requests
import calendar
import itertools
import mypaths
import random
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
from genChannelLineup import *


def doit_wrapper(cfg,printflg=False):
    try :
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
        # set variables
        serviceidlist = []
        timeout = 2
        var = 4
        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        pps_port = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        channel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        serviceidlist.append(unicode(channel2))
        upm_hosts =  [cfg['upm']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        printLog("Final list :"+ str(hosts_list),printflg)
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        prefix = cfg['basic_feature']['household_prefix']
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        #Ingest the Catalog to the CI Host
        channel = ChannelLineup(BoundaryInMinutes=1)
        eventtitle = 'traffickey120' 
        now = time.time()+10*60 #Set schedule to future 10 minutes
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=var,timeSlotCount=5,programIDPrefix=eventtitle)
        # ensure an even boundary since could skew by 1 minute if that statement uncommented
        now = int(now // (var * 60.0)) * (var * 60.0)   
        channel.postXmlData(ci_host,ci_port,startTime = now,timewindow=var)
        channel.writeXmlFiles(startTime = now,timewindow=var, suffix='_noskew')
        #now += 1*60    # uncomment to skew schedule by 1 minute
        #channel.postXmlData(ci_host,ci_port,startTime = now,timewindow=4)
        #channel.writeXmlFiles(startTime = now,timewindow=4, suffix='_1minskew')
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        #return 0
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
    except :
        message =  "Error Occured in configuration\n" + PrintException(True)
        print message 
        return 1
           
    for (cmdc_host,pps_host,upm_host) in hosts_list :
        try:
            grid_response = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
            print "Grid Response:\n" + json.dumps(json.loads(grid_response.content),indent=4,sort_keys=False)
            if grid_response:
                contentId_dict = get_currentandfuture_contentIddict(grid_response,eventtitle)
                print "contentId dict" + str(contentId_dict)
                if contentId_dict:
                    contentIdlist = get_contentIdlist_allcontentiddict_channellineup(contentId_dict,printflg) 
                    print "ContentId list" + str(contentIdlist)
                    if contentIdlist:
                        contentId = contentIdlist[0][0]
                        pps_headers = {
                            'Content-Type': 'application/json',
                            'Source-Type': 'WEB',
                            'Source-ID': '127.0.0.1',
                            }
                        payload = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (contentId)
                        result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,payload,contentId,timeout,printflg)
                        if result == "PASS":
                            verifybookingresult,verifybookingresponse = verify_booking(pps_port,protocol,pps_host,householdid,[contentId],timeout) 
                            if verifybookingresult == "PASS" and verifybookingresponse:
                                verifybookingcontent = json.loads(verifybookingresponse.content)
                                print "Booked Library" + json.dumps(verifybookingcontent,indent=4,sort_keys=False)
                                for items in verifybookingcontent:
                                    if items['scheduleInstance'] == contentId:
                                        contentstarttime = items['content']['broadcastDateTime']
                                        print "Content Start Time before changing metadata" + str(contentstarttime)
                                time.sleep(60)
                                #Ingest Event by skewing of 1 minute
                                channel_1 = ChannelLineup(BoundaryInMinutes=1)
                                channel_1.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=var,timeSlotCount=5,programIDPrefix=eventtitle)
                                # ensure an even boundary since could skew by 1 minute if that statement uncommented
                                now += 1*60    # uncomment to skew schedule by 1 minute
                                channel_1.postXmlData(ci_host,ci_port,startTime = now,timewindow=var)
                                channel_1.writeXmlFiles(startTime = now,timewindow=var, suffix='_1minskew')
                                print channel_1
                                length = channel_1.getTotalLength()
                                sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
                                #return 0
                                print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
                                time.sleep(sleep_channel)
                                grid_response1 = fetch_gridRequest_lessthancurrenttime(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
                                print "Grid Response:\n" + json.dumps(json.loads(grid_response1.content),indent=4,sort_keys=False)
                                verifybookingresult1,verifybookingresponse1 = verify_booking(pps_port,protocol,pps_host,householdid,[contentId],timeout)
                                if verifybookingresult1 == "PASS" and verifybookingresponse1:
                                    jsonverifybookingcontent = json.loads(verifybookingresponse1.content)
                                    print "Booked Library after second ingest" + json.dumps(jsonverifybookingcontent,indent=4,sort_keys=False)
                                    for items in jsonverifybookingcontent:
                                        if items['scheduleInstance'] == contentId:
                                            contentstarttime = items['content']['broadcastDateTime']
                                            print "Content Start Time after changing metadata" + str(contentstarttime)                
                                            return 0
        except :
            message =  "Error Occured in configuration\n" + PrintException(True)
            print message 
            return 1


if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    #read config file
    sa = sys.argv
    cfg = relative_config_file(sa,scriptName)
    if cfg['basic_feature']['print_cfg']:
         print "\nThe following configuration is being used:\n"
         pprint(cfg)
         print
    L = doit_wrapper(cfg, True)
    status_value = L 
    if status_value :
        exit(1)
    else :
        exit(0)


