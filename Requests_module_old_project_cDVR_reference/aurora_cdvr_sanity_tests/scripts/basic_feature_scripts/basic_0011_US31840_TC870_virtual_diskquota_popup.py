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


#######################################################################################
# Test Steps: Fail booking request if disk quota full
#STEP1:Ingest the catalog for 4 individual event of n minutes each 
#STEP2:Fetch the content ID of all the three event and diskquota for the first event 
#STEP3:Modify the diskquota as required by the first event booking , so that the storage quota is full
#STEP4:Do the pps booking for the first event verify that the event is successfully recorded 
#STEP5:Do pps booking for the second event , and verify that booking failed 
#STEP6:Delete the first successfull booking to empty storage quota 
#STEP7:Do the third pps booking , and verify that the booking is successfull
#######################################################################################
def doit(cfg, printflg=False):
    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        updatevalue = updatetimsresultsjson(cfg, start_time, end_time, rc, 'basic-feature')
        return updatevalue
    except:
        print "Error Occurred in Script \n"
        PrintException()
        return 1


def doit_wrapper(cfg, printflg=False):
    try:
        message = ""
        status = 3
        tims_dict = {
                 "TC870": ["US31840", message, status],
                 "TC869": ["US31839", message, status]
                }
        print "\nUS31840:As a SP, I want the viewer to receive an error message during booking if the booking fails due to exceeding the household storage quota limit"
        print "\nTC870:Virtual disk space full popup"
        print "\nUS31839:As a SP,I want to fail a booking request if there is not enough available space in the Household's storage quota"
        print "\nTC869:Fail booking request if disk quota full"

        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        check_test_flag = test_flag(cfg, "no_dataplane")
        if check_test_flag:
            message = "Skipped DataPlane test cases"
            print message
            tims_dict = update_tims_data(tims_dict, 2, message, ["TC870", "TC869"])
            return tims_dict

        #Initialize the Variables
        serviceidlist =[]
        timeout = 2
        uri_delete = None

        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        port_pps = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        upm_hosts = [cfg['upm']['host']]
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']   
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        prefix = cfg['basic_feature']['household_prefix']
        print "\n### STEP1: Ingest the catalog for 4 individual event of n minutes each ##########\n"
        eventtitle = "tc870" + str(random.randint(100, 199))
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        timeslotinminutes = cfg['test_channels']['shortProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1, timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=3, programIDPrefix=eventtitle)
        channel.postXmlData(ci_host, ci_port, startTime=post_time)
        channel.writeXmlFiles(startTime=post_time)
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
        diskquota_headers_hh = {
            'Content-Type': 'text/plain',
            'Source-Type': 'WEB',
            'Source-ID': '211.209.128.25',
            }
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
    except:
        message = "Testcase Failed: Error Occured in configuration" + PrintException(True)
        print message 
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC869","TC870"])
        return tims_dict
           
    for (cmdc_host, pps_host, upm_host) in hosts_list:
        try:
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg, port_pps, protocol, pps_host, householdid, pps_headers, timeout)
            print "\n### STEP2:fetch the content ID of all the three event and diskquota for the first event ####### \n"
            old_diskquota = fetch_full_details_diskquota(protocol, upm_host, port_upm, householdid, timeout, printflg=False)
            assert old_diskquota,"Testcase Failed: Unable to Fetch the Diskquota for the household"
            print "Original Diskquota is :", old_diskquota.content
            grid_response = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
            assert grid_response, "Testcase Failed: Unable to Fetch Grid Response"
            contentId_dict_all = get_contentIddict_bytitle(grid_response,eventtitle,['title'])
            print "ContentId dictionary from the grid response\n", str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
            event_contentId_list = sorted(contentId_dict_all.items(), key=lambda x:x[1])
            print "ContentId list after sorting\n", str(event_contentId_list)
            assert len(event_contentId_list) >=2, "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
            random_contentId = event_contentId_list[0][0]
            random_contentId_1 = event_contentId_list[1][0]
            random_contentId_2 = event_contentId_list[2][0]
            diskquota = event_contentId_list[0][1][2]
            payload1 =  """{
                "checkConflicts": true,
                "pvr": "nPVR",
                "scheduleInstanceId": "%s"
                }"""%(random_contentId)

            print "\n### STEP3: Modify the diskquota as required by the first event booking , so that the storage quota is full #####\n "
            diskquota1 = diskquota/1000
            diskquota = str(diskquota1)
            modifydiskquota = modify_diskQuota(cfg, protocol, upm_host, port_upm, householdid, diskquota, diskquota_headers_hh,
                                               timeout, printflg)
            assert modifydiskquota == "PASS", "Testcase Failed: Unable to Modify the Diskquota for the household"

            # Fetch the Booking Catalog based on the above result
            full_diskquota = fetch_full_details_diskquota(protocol, upm_host, port_upm, householdid, timeout, printflg)

            assert full_diskquota, "Testcase Failed: Unable to Fetch the Diskquota for the household"
            print "Full diskquota is ", full_diskquota.content
            print "\n### STEP4: Do the pps booking for the first event verify that the event is successfully recorded ####\n"
            result = do_PPSbooking(port_pps, protocol, pps_host, householdid, pps_headers, payload1, random_contentId, timeout, printflg)
            assert result == "PASS", "Testcase Failed: PPS Booking failed for the event contentId %s" %(random_contentId)

            print "PPS booking is successful for the event contentId %s" %(random_contentId)

            book_result, book_response = verify_booking(port_pps, protocol, pps_host, householdid, random_contentId, timeout)

            assert book_result, "Testcase Failed : Event not in Booking state"

            event_state = json.loads(book_response.content)
            for val in event_state:
                if val["scheduleInstance"] == random_contentId :
                    if val["state"] == "BOOKED" or val["state"] == "RECORDING":
                        printLog("Progam status for householdId " + householdid +" & " + random_contentId ,printflg)
                        uri_delete = val['uri']

            assert uri_delete, "Testcase Failed : Unable to get the URI of Event 1"

            event1_start_time = event_contentId_list[0][1][0]
            event1_end_time = event_contentId_list[0][1][1]
            print "Program starts broadcasting from ", str(event1_start_time), " (in epoch)"
            wait_till_start_time = get_timedifference(event1_start_time, printflg)
            print "Script will wait for ", str(wait_till_start_time/60), " minutes to start the recording"
            time.sleep(wait_till_start_time)
            time.sleep(recordingstatecheck_waittime)

            recordingresult, recordingresponse = verify_recording_state(port_pps, protocol, pps_host, householdid, random_contentId, timeout)

            assert recordingresult == "PASS" and recordingresponse, "Testcase Failed : Event is not in Recording state"
            print "Recording Started and Program broadcasting completes at ", str(event1_end_time), " (in epoch)"
            program_endtime = get_timedifference(event1_end_time, printflg)
            print "Program Recording completes in ", program_endtime, " seconds"
            time.sleep(program_endtime)
            time.sleep(recordedstatecheck_waittime)

            recorded_res, recorded_response = verify_recorded_state(port_pps, protocol, pps_host, householdid, random_contentId, timeout)

            assert recorded_res == "PASS", "Testcase Failed : Event is not in Recorded state"

            print "Event 1 is in Recorded state"

            print "Trying to attempt for second booking"
            payload2 = """{
                         "checkConflicts": true,
                         "pvr": "nPVR",
                         "scheduleInstanceId": "%s"
                         }"""%(random_contentId_1)
            full_diskquota1 = fetch_full_details_diskquota(protocol, upm_host, port_upm, householdid, timeout, printflg)
            assert full_diskquota1, "Testcase Failed : Unable to get the fetch full diskquota details"

            print "Full diskquota is ", full_diskquota1.content

            print "\n### STEP5: Do pps booking for the second event , and verify that booking failed due to insufficient quota  ######\n"
            result,response = do_PPSbooking_returnresponse(port_pps, protocol, pps_host, householdid, pps_headers, payload2, random_contentId_1,
                                                           timeout, printflg)
            assert result == "FAIL", "Testcase Failed : Seconds event is booked which is not expected"
            responsecontent = json.loads(response.content)

            assert response.status_code == 403, "Testcase Failed : Event 2 booking response code is not 403"
            assert responsecontent["message"] == "Disk Space Conflict Detected", "Testcase Failed : Event 2 booking failed due to unexpected reason"

            print "\n### STEP6: Delete the first successfull booking to empty storage quota  #######\n "
            ev1_delete = delete_PPSbooking(port_pps, protocol, pps_host, pps_headers, timeout, uri_delete, printflg)
            assert ev1_delete == "PASS", "Testcase Failed : Unable to delete the Event 1"

            #Do the Third PPS Booking and Verify
            print "\n### STEP7: Do the third pps booking , and verify that the booking is successful  #####\n "
            payload3 = """{
                    "checkConflicts": true,
                    "pvr": "nPVR",
                    "scheduleInstanceId": "%s"
                    }"""%(random_contentId_2)
            full_diskquota = fetch_full_details_diskquota(protocol, upm_host, port_upm, householdid, timeout, printflg)
            assert full_diskquota, "Testcase Failed : Unable to fetch full disk quota detail"
            print "Full diskquota is ", full_diskquota.content

            ev2_book_res, ev3_book_response = book_and_verify(port_pps, protocol, pps_host, householdid, pps_headers, payload3,
                                                              random_contentId_2, catalog_fetch_delay=2, timeout=timeout)

            assert ev2_book_res == "PASS", "Testcase Failed : Event 3 is not booked successfully"

            message = "Testcase Passed : Event 1 is deleted and Event 3 is booked successfully"

            tims_dict = update_tims_data(tims_dict, 0, message, ["TC869", "TC870"])

        except AssertionError as ae:
            message = str(ae)
            debug_print_log(port_pps, protocol, pps_host, householdid, timeout)
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC869", "TC870"])

        except:
             message = "Testcase Failed: Error Occurred in Script\n", PrintException(True)
             debug_print_log(port_pps, protocol, pps_host, householdid, timeout)
             tims_dict = update_tims_data(tims_dict, 1, message, ["TC869","TC870"])

        finally:
            cleanup_household(cfg, port_pps, protocol, pps_host, householdid, pps_headers, timeout)
            print message
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
    if status_value:
        if 1 in status_value or 3 in status_value:
            exit(1)
        else:
            exit(0)
    else:
        exit(1)

