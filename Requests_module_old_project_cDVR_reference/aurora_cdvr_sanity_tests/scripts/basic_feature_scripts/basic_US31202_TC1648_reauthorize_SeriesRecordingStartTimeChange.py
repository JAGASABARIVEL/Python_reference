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

######################################################################################################################################################################################
# TC1648: Re-authorize a household for Cloud DVR, ensure new series bookings result in recordings starting at the re-authorization date/time 
#TEST STEPS:
#STEP1: Ingest the Series of 3 Episodes on one channel with the post time of 3 minutes  and difference between Episode1 and Episode2 is 3 minutes
#STEP2:	Do the Series Booking and Verify the Booked Catalog
#STEP3:	Disable the CDVR Services before first episode starts,
#step4a:ingest episode 4 
#STEP4:	Before the Episode2 starts broadcasttime, reenable back the CDVR services
#STEP5:	Verify the episode4,Episode2 is in recording and wait till the Episode3 completes recording
#STEP6:	Verify the recorded library has Episode2 and Episode3,episode4 in Recorded state
#STEP7: Re enable the services back irrespective of Pass or Fail
#######################################################################################################################################################################################

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
                 "TC1648":["US31202",message,status]
                }
        print "\nUS31202: Suspend a household"
        print "\nTC1648: A household that has been authorized for cDVR has cDVR service de-authorized for a period of time. cDVR services are then re-authorized. The household should not have to take any additional action for pre-existing series bookings to result in new bookings when episodes of the series appear in metadata"
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
        tims_log = []
        #Initialize the Variables
        serviceidlist =[]
        timeout = 10
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
        print "\n\n###STEP1: Ingest the Series of 3 Episodes on one channel with the post time of 3 minutes  and difference between Episode1 and Episode2 is 3 minutes ########################\n"
        title = 'Serreauth' + str(random.randint(100,199))
        post_time = time.time()+240
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1, timeSlotLengthMinutes=5,
                              showID=title, episodeCount=1, startEpisodeNumber=1, timeSlotCount=1)
        endtime1 = channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length1 = channel.getTotalLength()
        endtime2 = endtime1 + 180
        channel2 = ChannelLineup(BoundaryInMinutes=0)
        channel2.add_to_lineup(serviceId=channel1, timeSlotLengthMinutes=5,
                              showID=title, episodeCount=2, startEpisodeNumber=2, timeSlotCount=2)
        endtime2 = channel2.postXmlData(ci_host,ci_port,startTime = endtime2)
        channel2.writeXmlFiles(startTime = endtime2)
        print channel2
        length2 = channel2.getTotalLength()

        length = length1 + length2
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
        tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
        return tims_dict
    for (cmdc_host,pps_host,upm_host) in hosts_list :
     try:
        print "Cleaning up the household bookings and recordings before testcase execution"
        print_failedrecording_catalog(port_pps,protocol,pps_host,householdid,timeout)
        cleanup_householdid_items(port_pps,protocol,pps_host,householdid,pps_headers,timeout)
        print "\n\n###STEP2: Do the Series Booking and Verify the Booked Catalog ###############################################################\n"
        grid_response = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
        if grid_response:
          contentId_dict_all = get_contentIddict_bytitle(grid_response,title,['title'])
          print contentId_dict_all
          if contentId_dict_all :
              event_contentId_list = sorted(contentId_dict_all.items(), key=lambda x:x[1])
              if len(event_contentId_list) >2:
                  for items in event_contentId_list:
                      contentid_list.append(items[0])
                      start_time_list.append(items[1][0])
                      end_time_list.append(items[1][1])
                      duration_list.append(items[1][2])
                  payload1 =  """{
                        "checkConflicts": true,
                        "pvr": "nPVR",
                        "scheduleInstanceId": "%s",
                        "recurrence":"SERIES"
                        }"""%(contentid_list[0])
              else:
                    message =  "Testcase failed : Error in retrieving Content ID Dictionary"
                    print message 
                    tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
                    return tims_dict
          else:
                message =  "Testcase failed : Error in retrieving Full Content ID Dictionary"
                print message 
                tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
                return tims_dict
        else:
             message =  "Testcase failed : Error in retrieving Grid Response"
             print message 
             tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
             return tims_dict
        result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload1,contentid_list[0],timeout,printflg)
        if result == "PASS":
          print contentid_list
          time.sleep(20)
          verify_booking_result,bookedcatalogresponse = verify_booking(port_pps,protocol,pps_host,householdid,contentid_list,timeout)
          if verify_booking_result == "PASS" :
            print "\n\n###STEP3: Disable the CDVR Services before first episode starts,verify here that first episode is not in RECORDING state and wait till the first episode gets completed #####################################################\n"
            deleteserviceresult = delete_HouseholdEnabledService( protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
            if deleteserviceresult == "PASS":
                print "Deleting the Service for the Household is successful"
            else:
                 message = "Testcase failed :Testcase failed :Failed to Delete the Service for the Household"
                 print message
                 tims_dict = update_tims_data(tims_dict, 1, message, ["TC1648"])
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
                        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1648"])
                        return tims_dict
            else:
                 set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
                 message = "Testcase failed :Testcase failed :Failed to Delete the Service for the Household"
                 print message
                 tims_dict = update_tims_data(tims_dict, 1, message, ["TC1648"])
                 return tims_dict
            print contentid_list
            time.sleep(20)
            verify_booking_result,bookedcatalogresponse = verify_booking(port_pps,protocol,pps_host,householdid,contentid_list,timeout)
            if verify_booking_result == "PASS" :
                print  "Testcase : Booked catalog has all the events after disabling cDVR services"
                program_starttime = get_timedifference(start_time_list[0],printflg)
                print "Recording will start in " + str(program_starttime)+ "seconds"
                time.sleep(program_starttime)
                time.sleep(recordingstatecheck_waittime)
                time.sleep(recordingstatecheck_waittime)
                recordingcontentresult,recordingcontentresponse = verify_recording_state(port_pps,protocol,pps_host,householdid,contentid_list[0],timeout)
            else:
                set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
                message =  "Testcase failed : Booked catalog does not have all the events after disabling cDVR services"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
                return tims_dict
          else:
              set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
              message =  "Testcase failed : Booked catalog does not have all the events"
              print message
              tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
              return tims_dict
        else:
            message =  "Testcase failed : PPS Booking failed for the series"
            print message 
            tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
            return tims_dict
        if recordingcontentresult == "FAIL":
            set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
            print "Recording has not started for the first episode, will wait till the time for first episode ellapses"
            program_endtime = get_timedifference(end_time_list[0],printflg)
            print "Episode1 Recording will end in " + str(program_endtime)+ "seconds"
            time.sleep(program_endtime)
            print "Broadcasting time for episode 1 is ellapsed"    
        else:
            set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
            message =  "Testcase Failed : Recording has started for the episode 1, which was not expected"
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
            return tims_dict

        print "\n\n###STEP4: Before the Episode2 starts broadcasttime, reenable back the CDVR services ####################################################\n"
        set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
        jsonrecordingcontent = json.loads(recordingcontentresponse.content)
        printLog("Recording Content Response for the Content Id\n" + json.dumps(json.loads(recordingcontentresponse.content),indent=4,sort_keys=False),printflg)
        program_starttime2 = get_timedifference(start_time_list[1],printflg)
        print "Recording for episode 2 will start in " + str(program_starttime2)+ "seconds"
        time.sleep(program_starttime2)
        time.sleep(recordingstatecheck_waittime)
        time.sleep(recordingstatecheck_waittime)
        print "\n\n###STEP5: Verify the Episode2 is in recording and wait till the Episode3 completes recording #######################################\n"
        recordingcontentresult2,recordingcontentresponse2 = verify_recording_state(port_pps,protocol,pps_host,householdid,contentid_list[1],timeout)
     
        if recordingcontentresult2 == "PASS" :
            print "Second episode is getting recorded"
            program_endtime2 = get_timedifference(end_time_list[-1],printflg)
            print "Series Recording will end in " + str(program_endtime2)+ "seconds"
            time.sleep(program_endtime2)
            time.sleep(recordingstatecheck_waittime)
            print "Series is completed recording"           
        else:
            set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
            message =  "Testcase Failed : Recording has not started for the episode 2"
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
            return tims_dict
        contentid_list2 = contentid_list
        contentid_list2.remove(contentid_list2[0])
        print "content id list for episode1 and episode2: ", contentid_list2 
        print "\n\n###STEP6: Verify the recorded library has Episode2 and Episode3 in Recorded state ###################################################\n"
        recordedcontentresult,recordedcontentresponse = verify_recorded_state(port_pps,protocol,pps_host,householdid,contentid_list2,timeout)
        print "\n\n###STEP7: Re enable the services back irrespective of Pass or Fail ####################################################\n"
        set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
        if recordedcontentresult == "PASS":
            message = "Testcase Passed: Episode1 and episode2 recorded succesfully"
            print message
            tims_dict = update_tims_data(tims_dict,0,message,["TC1648"])
            return tims_dict
        else:
            message = "Testcase Failed: Episode1 and episode2 not recorded succesfully"
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
            return tims_dict
     except :
             if cDVR_service_list:
                 set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
             message =  "Testcase failed : Error Occured \n" + PrintException(True)
             print message 
             tims_dict = update_tims_data(tims_dict,1,message,["TC1648"])
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


