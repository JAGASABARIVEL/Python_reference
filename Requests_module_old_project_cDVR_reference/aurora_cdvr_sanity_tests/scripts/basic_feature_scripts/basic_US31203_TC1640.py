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
import re
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
from genChannelLineup import *


#######################################################################################
# De-authorize a household for Cloud DVR, ensure existing bookings do not result in recordings
#TEST STEPS:
#STEP1.Ingest the Event of 3 Minutes with the Post Time of 5 Minutes
#STEP2.Do the PPS Booking for the Household
#STEP3.Get the Enabled Services for the same Household and disable all CDVR related services
#STEP4.Verify the Event is in the Booked Catalog and the same state.
#STEP5.Wait till the broadcasttime and the state change delay and check that the booking should not go in recording state since CDVR service is disabled for the Household
#STEP6.Enable back all the CDVR services and update the results irrespective of pass or fail

#######################################################################################
def doit(cfg,printflg=True):
    try :
        start_time = time.time()
        rc = doit_wrapper(cfg,printflg)
        end_time = time.time()
        time_value = end_time - start_time
        time_value = round(time_value , 6 )
        time_value = str(time_value)
        filename =  cfg['test_results']['filename']
        data = {
            "config": {
                "labname" : cfg['LABNAME'] ,
                "extraconf" : str(cfg['EXTRACONF']) ,
                "gitrepo" : cfg['GITREPO'] ,
                "gitlastcommit" :  cfg['GITLASTCOMMIT'] ,
                "description" : cfg['lab-description']
               }
            }
        timsResults = JsonReadWrite(filename)
        timsResults.writeDictJson(data)
        status_value = []
        for key,val in dict.items(rc):
            TC = key 
            US = val[0]
            message = val[1]
            status_value.append(val[2])
            if val[2] == 0 or val[2] == 2:
                status = "PASS"
            elif val[2] == 3:
                status = "Not Run"
            else:
                status = "FAIL"
            name  =  os.path.basename(__file__)[:-3]
            # message will eventually be the last log message but this is a proof of concept
            results = {
                "CF": "",
                "I": "Core DVR Functionality",
                "MF": "",
                "TC": TC,
                "US": US,
                "message": message,
                "name": name,
                "status": status,
                "time": time_value
                }
            timsResults.appendListToKey('testsuite:basic-feature', results)
        if status_value :
            if ( 1 in status_value ) or ( 3 in status_value) :
                return (1)
            elif (4 in status_value) or (2 in status_value):
                return (2)
            else :
                return (0)
        else :
             print "status_value not present,Error in return code "
             return 1
    except:
          print  "Error Occurred in TIMS log \n"
          PrintException()
          return (1)

def doit_wrapper(cfg,printflg=False):
    try :
        message = ""
        status = 3
        tims_dict = {
                 "TC1640":["US31203",message,status],
                 "TC1643":["US31203",message,status]
                }
        print "\nUS31203: Create a household"
        print "\nTC1640:De-authorize a household for Cloud DVR, ensure existing bookings do not result in recordings"
        print "\nTC1643:De-authorize a household for Cloud DVR, ensure existing bookings are retained"
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
        tims_log = []
        #Initialize the Variables
        serviceidlist =[]
        timeout = 10
        full_diskquota = None
        full_diskquota1 = None
        booking_catalog = None
        recordedcontentresponse = None
        grid_response = None
        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        port_pps = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        channel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        serviceidlist.append(unicode(channel2))
        upm_hosts =  [cfg['upm']['host']]
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']   
        prefix = cfg['basic_feature']['household_prefix']
        print "### STEP1 Ingest the Event of 3 Minutes with the Post Time of 5 Minutes##################################### \n \n "
        eventtitle = 'Event' + str(random.randint(100,199))
        post_time = time.time()+240
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=5,timeSlotCount=2,programIDPrefix = eventtitle)
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
        pps_headers = {
                 'Content-Type': 'application/json',
                 'Source-Type': 'WEB',
                 'Source-ID': '127.0.0.1',
                 }
        upm_headers = {
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Accept': 'application/json',
        }

        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        printLog("Final list :"+ str(hosts_list),printflg)
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        contentid_list= []
        start_time_list = []
        end_time_list = []
        duration_list = []
        cDVR_service_list= ["CDVR","ALLOW-CDVR-TIME-BASED-RECORDING"]
        print cDVR_service_list
        cDVR_service_list_1 = json.dumps(cDVR_service_list)
    except :
        message =  "Testcase failed : Error Occured in configuration\n" + PrintException(True)
        print message 
        tims_dict = update_tims_data(tims_dict,1,message,["TC1640","TC1643"])
        return tims_dict
    for (cmdc_host,pps_host,upm_host) in hosts_list :
     try:
        print "Cleaning up the household bookings and recordings before testcase execution"
        print_failedrecording_catalog(port_pps,protocol,pps_host,householdid,timeout)
        cleanup_householdid_items(port_pps,protocol,pps_host,householdid,pps_headers,timeout)
        print "### STEP2 Do the PPS Booking for the Household  ###################################### \n \n "
        grid_response = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
        if grid_response:
          contentId_dict_all = get_contentIddict_bytitle(grid_response,eventtitle,['title'])
          if contentId_dict_all :
              event_contentId_list = sorted(contentId_dict_all.items(), key=lambda x:x[1])
              if len(event_contentId_list) >=1:
                  for items in event_contentId_list:
                        contentid_list.append(items[0])
                        start_time_list.append(items[1][0])
                        end_time_list.append(items[1][1])
                        duration_list.append(items[1][2])
                  payload1 =  """{
                        "checkConflicts": true,
                        "pvr": "nPVR",
                        "scheduleInstanceId": "%s"
                        }"""%(contentid_list[0])
              else:
                    message =  "Testcase failed : Error in retrieving First Random Content ID Dictionary"
                    print message 
                    tims_dict = update_tims_data(tims_dict,1,message,["TC1640","TC1643"])
                    return tims_dict
          else:
                message =  "Testcase failed : Error in retrieving First Full Content ID Dictionary"
                print message 
                tims_dict = update_tims_data(tims_dict,1,message,["TC1640","TC1643"])
                return tims_dict
        else:
             message =  "Testcase failed : Error in retrieving First Grid Response"
             print message 
             tims_dict = update_tims_data(tims_dict,1,message,["TC1640","TC1643"])
             return tims_dict
        result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload1,contentid_list[0],timeout,printflg)
        if result == "PASS":
            print "### STEP 3 .Get the Enabled Services for the same Household and disable all CDVR related services \n\n"
            deleteserviceresult = delete_HouseholdEnabledService( protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
            if deleteserviceresult == "PASS":
                print "Deleting the Service for the Household is successful"
            else:
                 message = "Testcase failed :Testcase failed :Failed to Delete the Service for the Household"
                 print message
                 tims_dict = update_tims_data(tims_dict, 1, message, ["TC1640","TC1643"])
                 return tims_dict
            householdservicelist = get_HouseholdEnabledServices( protocol, upm_host, port_upm, householdid, upm_headers, timeout)
            if householdservicelist :
                servicelist = json.loads(householdservicelist)
                print "Household Service List" + str(servicelist)
                for service in cDVR_service_list:
                    if service in servicelist:
                        set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
                        message = "Testcase failed :Failed to Delete the Service for the Household"
                        print message
                        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1640","TC1643"])
                        return tims_dict
            else:
                 set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
                 message = "Testcase failed :Testcase failed :Failed to Delete the Service for the Household"
                 print message
                 tims_dict = update_tims_data(tims_dict, 1, message, ["TC1640","TC1643"])
                 return tims_dict
            #time.sleep (recordingstatecheck_waittime)
            print "### STEP4 . Verify the Event is in the Booked Catalog and the same state."
            verify_booking_result,bookedcatalogresponse = verify_booking(port_pps,protocol,pps_host,householdid,contentid_list[0],timeout)
            if verify_booking_result == "PASS" :
                message =  "Testcase : Booked catalog does  have all the events"
                print message
                tims_dict = update_tims_data(tims_dict,0,message,["TC1643"])
            else:
                set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
                message =  "Testcase failed : Booked catalog does not have all the events"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC1640","TC1643"])
                return tims_dict
        else:
            message =  "Testcase failed : First PPS Booking failed"
            print message 
            tims_dict = update_tims_data(tims_dict,1,message,["TC1640","TC1643"])
            return tims_dict
        print "### STEP5.Wait till the broadcasttime and the state change delay and check that the booking should not go in recording state since CDVR service is disabled for the Household \n\n"
        program_starttime = get_timedifference(start_time_list[0],printflg)
        print "Recording will start in " + str(program_starttime)+ "seconds"
        time.sleep(program_starttime)
        time.sleep(recordingstatecheck_waittime)
        recordingcontentresult,recordingcontentresponse = verify_recording_state(port_pps,protocol,pps_host,householdid,contentid_list[0],timeout)
        if recordingcontentresult == "PASS":
             set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
             jsonrecordingcontent = json.loads(recordingcontentresponse.content)
             printLog("Recording Content Response for the Content Id\n" + json.dumps(json.loads(recordingcontentresponse.content),indent=4,sort_keys=False),printflg)
             message =  "Testcase failed : Recording has  started for the event"
             print message
             tims_dict = update_tims_data(tims_dict,1,message,["TC1640"])
             return tims_dict
        else:
             set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
             message =  "Testcase passes : Recording has not started for the event"
             print message
             tims_dict = update_tims_data(tims_dict,0,message,["TC1640"])
             return tims_dict
     except :
             if cDVR_service_list:
                 set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
             message =  "Testcase failed : Error Occured \n" + PrintException(True)
             print message 
             tims_dict = update_tims_data(tims_dict,1,message,["TC1640","TC1643"])
             return tims_dict


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
    status_value = []
    for key,val in dict.items(L):
        status_value.append(val[2])
    if status_value :
        if ( 1 in status_value ) or ( 3 in status_value) :
             exit (1)
        else:
             exit(0)
    else :
          exit(1)


