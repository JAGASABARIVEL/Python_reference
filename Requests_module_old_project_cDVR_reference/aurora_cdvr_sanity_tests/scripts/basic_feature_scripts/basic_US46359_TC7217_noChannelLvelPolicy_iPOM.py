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
import datetime as DT

#######################################################################################
#TEST STEPS: Hybrid Copy - No channel level policy in iPOM - iPOM default is Common
# STEP1. Create 3 Households
# STEP2. Ingest 1 Event of n minutes with posttime of n mins
# STEP3. Do PPS booking for the event in all 3 households
# STEP4. Wait till the recording completes
# STEP5. Verify the Event recordings present in all 3 households
# STEP6: Get the contentplayuri from the Recorded Catalog on all 3 Households
# STEP7: Get the recordingid using the contentplayuri and RM playback API for all 3 Household recordings
# STEP8: Get the streamid/isid/batchid/actualstarttime/actualendtime for all recordingids from STEP7 using the VMR API Request
# STEP9: Verify actualstarttime and actualendtime from STEP8 matching for all household recordingids successfully
# STEP10: Get all the segments using the streamid/actualstarttime and actualendtime from the VMR API Request and store it in a temp file
# STEP11: Verify 200 OK Response in the COS Active Storage with 'X-Fanout-Copy-Index': '0' using isid/segmentid/batchid on all the segments from a temp file and 416 Response with 'X-Fanout-Copy-Index':1
# STEP12: Revert back the households to its original state
#######################################################################################
def doit(cfg,printflg=False):
    try :
        start_time = time.time()
        set_errorlogging()
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
            elif val[2] == 4:
                status = "Unsupported"
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
          print  "Error Occurred in script \n"
          PrintException()
          return (1)

def doit_wrapper(cfg,printflg=False):
    try :
        message = ""
        status = 3
        tims_dict = {
            "TC17217": ["US46359", message, status],
        }
        print "\nUS46359: Test Hybrid Common and Unique Copy Functionality"
        print "\nTC17217: Hybrid Copy - No channel level policy in iPOM - iPOM default is Common"
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
        # Initialize the Variables
        serviceidlist = []
        timeout = 2
        full_diskquota = None
        grid_response = None
        contentid_list = []
        start_time_list = []
        end_time_list = []
        duration_list = []
        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        port_pps = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        available_channels = cfg['cornercase-channelsets']['set2']
        channel1 = cfg['test_channels'][available_channels[0]]['ServiceId']
        serviceidlist.append(unicode(channel1))
        upm_hosts = [cfg['upm']['host']]
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']
        fetch_bookingCatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        prefix = cfg['basic_feature']['household_prefix']
        prmsupportedflag = cfg['prm_supported']
        proxyhostcheckflag = cfg['proxyHostNeeded']
        proxy_host = cfg['proxyhost']['host']
        proxy_port = cfg['proxyhost']['port']
        contentplayback_host = cfg['contentplayback']['host']
        contentplayback_port = cfg['contentplayback']['port']
        contentplayback_url = cfg['contentplayback']['url']
        rm_host = cfg['rm']['host']

        print "### STEP1: Ingest 1 Event of n minutes with posttime of n mins to the CI Host ### \n \n "
        eventtitle_1 = 'indieEvent' + str(random.randint(100, 199))
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['shortProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1, timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=1, programIDPrefix=eventtitle_1)
        ingest_endtime = channel.postXmlData(ci_host, ci_port, startTime=post_time)
        channel.writeXmlFiles(startTime=post_time)
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
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
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        hosts_list = list(itertools.product(cmdc_hosts, pps_hosts, upm_hosts))
        printLog("Final list :" + str(hosts_list), printflg)
        householdlimit = cfg['basic_feature']['households_needed']
        index_1 = 01
        index_2 = 02
        index_3 = 03
        print "STEP 2: Create 3 households"
        householdid_1 = prefix + str(index_1)
        householdid_2 = prefix + str(index_2)
        householdid_3 = prefix + str(index_3)
        householdid_list = [householdid_1, householdid_2, householdid_3]
    except:
        message = "Testcase Failed: Error Occured in configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC17217"])
        return tims_dict

    for (cmdc_host, pps_host, upm_host) in hosts_list:
        try:
            print "Cleaning up the household bookings and recordings before testcase execution"
            for householdid in householdid_list:
                cleanup_household(cfg, port_pps, protocol, pps_host, householdid, pps_headers, timeout)
            grid_response = fetch_gridRequest(catalogueId, protocol, cmdc_host, port_cmdc, serviceidlist, region, timeout, printflg=False)
            assert grid_response, "Testcase Failed: Unable to Fetch Grid Response"

            print "### STEP3:Do the PPS Booking for the same event on 3 Households ### \n \n "
            contentId_dict_all = get_contentIddict_bytitle(grid_response, eventtitle_1, ['title'])
            print "ContentId dictionary from the grid response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
            event_contentId_list = sorted(contentId_dict_all.items(), key=lambda x: x[1])
            print "ContentId list after sorting\n" + str(event_contentId_list)
            assert (len(event_contentId_list) >= 1), "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
            for items in event_contentId_list:
                contentid_list.append(items[0])
                start_time_list.append(items[1][0])
                end_time_list.append(items[1][1])
                payload1 = """{
                            "checkConflicts": true,
                            "pvr": "nPVR",
                            "scheduleInstanceId": "%s"
                        }""" % (items[0])
                print payload1

            assert contentid_list, "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
            booking_pass_counter = 0
            for householdid in householdid_list:
                print "### Verify the Booked catalog of all 3 households which has event present ### \n \n "
                result = do_PPSbooking(port_pps, protocol, pps_host, householdid, pps_headers, payload1, contentid_list[0], timeout, printflg)
                assert result == "PASS", "Testcase Failed: PPS Booking failed for the event contentId %s" % (contentid_list[0])
                print "PPS booking is successful for the event contentId %s" % (contentid_list[0])
                time.sleep(fetch_bookingCatalog_delay)
                verify_booking_result, bookedcatalogresponse = verify_booking(port_pps, protocol, pps_host, householdid, contentid_list[0], timeout)
                for i in range(5):
                    if verify_booking_result == "PASS":
                       break
                    else:
                        verify_booking_result, bookedcatalogresponse = verify_booking(port_pps, protocol, pps_host, householdid, contentid_list[0], timeout)
                assert verify_booking_result == "PASS", "Testcase Failed: Unable to Verify Booked Catalog"
                print "PPS Booking is successful and verified"
                booking_pass_counter = booking_pass_counter + 1

            assert booking_pass_counter == len(householdid_list), "Testcase Failed: PPS booking is not successfully or verified for three household"
            print "booking is successful for all the households"

            print "### STEP4: Wait till the recording completes  ###\n \n "
            recorded_pass_counter = 0
            program_endtime = get_timedifference(end_time_list[0], printflg)
            print "Recording will end in " + str(program_endtime) + "seconds"
            time.sleep(program_endtime)
            time.sleep(recordedstatecheck_waittime)
            time.sleep(30)
            contentURI_list=[]

            print "### STEP5: Verify the Event recordings present in all 3 households  ###\n \n "
            for householdid in householdid_list:
                recordedcontentresult, recordedcontentresponse = verify_recorded_state(port_pps, protocol, pps_host, householdid, contentid_list[0], timeout) #get 3 URI
                for i in range(5):
                    if recordedcontentresult == "PASS":
                       break
                    else:
                       print "3 mins delay added"
                       time.sleep(180)
                       recordedcontentresult, recordedcontentresponse = verify_recorded_state(port_pps, protocol, pps_host, householdid, contentid_list[0], timeout)
                assert recordedcontentresult == "PASS", "Testcase Failed : Unable to Verify Recorded Catalog"
                recorded_pass_counter = recorded_pass_counter + 1

            assert recorded_pass_counter == len(householdid_list), "Testcase Failed : Unable to Verify Recorded Catalog for all the three household"
            print "event is successfully recorded for all the three household"
            print "### STEP7: Get the recordingid using the contentplayuri and RM playback API for all 3 Household recordings ### \n \n "
            print "### STEP8:Get the streamid/isid/batchid/actualstarttime/actualendtime for all recordingids from STEP7 using the VMR API Request ### \n \n "
            print "### STEP9: Verify actualstarttime and actualendtime from STEP8 matching for all household recordingids successfully ### \n \n "
            print "### STEP10: Get all the segments using the streamid/actualstarttime and actualendtime from the VMR API Request and store it in a temp file  #### \n \n "
            commoncopy_result,commoncopy_response = verify_common_unique_copy(cfg, pps_host,port_pps, protocol, householdid_list,contentid_list, timeout=2, fanout = 1,
                                                         common_copy=True)
            print commoncopy_result,commoncopy_response
            print "### STEP11: Verify 200 OK Response in the COS Active Storage with 'X-Fanout-Copy-Index': '0' using isid/segmentid/batchid on all the segments from a temp file and 416 Response with 'X-Fanout-Copy-Index':1   ### \n \n "
            assert commoncopy_result,"Testcase Failed: FanOut value is not 0"
            message = "Testcase Passed: COS have been successfully verified"
            print message
            tims_dict = update_tims_data(tims_dict, 0, message, ["TC17217"])

        except AssertionError as ae:
            message = str(ae)
            print message
	    debug_print_log(port_pps, protocol, pps_host, householdid, timeout)
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC17217"])

        except Exception as e:
            message = str(e)
            print message
	    debug_print_log(port_pps, protocol, pps_host, householdid, timeout)
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC17217"])

        finally:
            print "#### STEP13: Revert back the original conditions, verify the results ####"
            for householdid in householdid_list:
                cleanup_household(cfg,port_pps, protocol, pps_host, householdid, pps_headers, timeout)
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
