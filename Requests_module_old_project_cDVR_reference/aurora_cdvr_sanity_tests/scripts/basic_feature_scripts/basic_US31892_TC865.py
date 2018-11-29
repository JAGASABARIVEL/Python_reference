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
from getCatalogServices import getCdvrServiceIds
from getOffers import getCdvrSubscriptionOffers
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
from genChannelLineup import *

#########################################################################################################################################################
# TC1077: Book series recording, user set to keep only the last "n" episodes of a series recording and auto-delete all others

#STEP1: Ingest Series with 6 Episodes of 2 Minutes with the post time to CI Host (Difference between Episode5 and Episode6 is 3 minutes)
#STEP2: Fetch the grid request and do the Series Booking with the First Episode ContentId
#STEP3: Verify the Booked Catalog and see all 6 Episodes are in Booked State
#STEP4: Set the "recordingsToKeep":5 using "PUT" method with the {item}/recurrence/recordingsToKeep  
#STEP5: Verify the first episode in Recording State and wait till 5 Episodes completes recording
#STEP6: Verify the Recorded Library and see all 5 Episodes are in Recorded State. Get the contentId of Episode#1 which is oldest. 
#STEP7: Wait till 6th Episode completes recording and verify Episode#1 is not in recorded library and Episode#6 is in the recorded library
#########################################################################################################################################################

def doit(cfg, printflg=True):
    try:
        start_time = time.time()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        time_value = end_time - start_time
        time_value = round(time_value, 6)
        time_value = str(time_value)
        filename = cfg['test_results']['filename']
        data = {
            "config": {
                "labname": cfg['LABNAME'],
                "extraconf": str(cfg['EXTRACONF']),
                "gitrepo": cfg['GITREPO'],
                "gitlastcommit":  cfg['GITLASTCOMMIT'],
                "description": cfg['lab-description']
            }
        }
        timsResults = JsonReadWrite(filename)
        timsResults.writeDictJson(data)
        status_value = []
        for key, val in dict.items(rc):
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
            name = os.path.basename(__file__)[:-3]
            # message will eventually be the last log message but this is a
            # proof of concept
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
        if status_value:
            if (1 in status_value) or (3 in status_value):
                return (1)
            elif (4 in status_value) or (2 in status_value):
                return (2)
            else:
                return (0)
        else:
            print "status_value not present "
            return 1
    except:
        print "Error Occurred in script \n"
        PrintException()
        return (1)


def doit_wrapper(cfg, printflg=False):
    message = ""
    status = 3
    tims_dict = {
        "TC865": ["US31892", message, status]
    }
    print tims_dict

    print "\n US31892: As a viewer, I want to keep only the last 'n' episodes of a series recording and auto-delete all others"
    print "\n TC865: Only keep last N episodes of a Series (Recurring) Recording"
    try:
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        # Initialize the variables
        timeout = 10
        serviceidlist = []
        grid_response = None
        contentid_list = []
        startTime_list = []
        endTime_list = []
        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        pps_port = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        bookingCatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        booked_to_recording_delay = cfg['pps']['booked_to_recording_delay']
        recording_to_recorded_delay = cfg['pps']['recording_to_recorded_delay']
        title = 'serlatrec' + str(random.randint(1, 99))
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        upm_hosts = [cfg['upm']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        prefix = cfg['basic_feature']['household_prefix']
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0, householdlimit - 1)
        householdid = prefix + str(index)
        hosts_list = list(itertools.product(cmdc_hosts, pps_hosts, upm_hosts))
        printLog("Final list :" + str(hosts_list), printflg)
        print "\n\n###STEP1:Ingest Series with 6 Episodes of 2 Minutes with the post time to CI Host (Difference between Episode5 and Episode6 is 3 minutes) \n"
        post_time = time.time() + 120
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg[
            'ci']['ingest_delay_factor_per_minute']
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1, timeSlotLengthMinutes=3,
                              showID=title, episodeCount=5, startEpisodeNumber=1, timeSlotCount=5)
        ingest_endtime = channel.postXmlData(
            ci_host, ci_port, startTime=post_time)
        ingest_endtime = int(ingest_endtime) + 180
        channel.writeXmlFiles(startTime=post_time)
        print channel
        length1 = channel.getTotalLength()
        channel2 = ChannelLineup(BoundaryInMinutes=0)
        channel2.add_to_lineup(serviceId=channel1, timeSlotLengthMinutes=2,
                              showID=title, episodeCount=1, startEpisodeNumber=6, timeSlotCount=1)
        last_ingest_endtime = channel2.postXmlData(
            ci_host, ci_port, startTime=ingest_endtime)
        channel2.writeXmlFiles(startTime=ingest_endtime)
        print channel2
        length2 = channel2.getTotalLength()
        length = length1 + length2
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute

        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
    except:
        message = "Error occured in configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC865"])
        return tims_dict

    else:
        for (cmdc_host, pps_host, upm_host) in hosts_list:
            try:
                print "Cleaning up the household bookings and recordings before testcase execution"
                cleanup_householdid_items(
                    pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                print "\n\n###STEP2: Fetch the grid request and do the Series Booking with the First Episode ContentId \n"
                grid_response = fetch_gridRequest(
                    catalogueId, protocol, cmdc_host, port_cmdc, serviceidlist, region, timeout, printflg=False)
                if grid_response:
                    contentid_dict = get_contentIddict_bytitle(
                        grid_response, title)
                    print contentid_dict
                    if contentid_dict:
                        contentid_sorted = sorted(
                            contentid_dict.items(), key=lambda x: x[1])
                        print contentid_sorted
                    else:
                        message = "Error in retrieving contentid_dict"
                        print message
                        tims_dict = update_tims_data(
                            tims_dict, 1, message, ["TC865"])
                        return tims_dict
                    if len(contentid_sorted) >= 6:
                        print "Content id details of event in sorted manner: ", contentid_sorted
                    else:
                        message = "Sorted content id list could not be fetched"
                        print message
                        tims_dict = update_tims_data(
                            tims_dict, 1, message, ["TC865"])
                        return tims_dict

                    for items in contentid_sorted:
                        contentid_list.append(items[0])
                        startTime_list.append(items[1][0])
                        endTime_list.append(items[1][1])

                    payload = """
                    {
                      "scheduleInstanceId" : "%s",
                      "checkConflicts" : true,
                      "pvr":"nPVR",
                      "recurrence":"SERIES" 
                      }""" % (contentid_list[0])
                    print "List of all content ids for booking: ", contentid_list
                    print"\nPPS booking is Doing for \n householdId %s  and its program id is %s" % (householdid, contentid_list[0])                   
                    event_booking_result, event_booking_catalog = book_and_verify(
                        pps_port, protocol, pps_host, householdid, pps_headers, payload, contentid_list[0], contentid_list, bookingCatalog_delay, timeout)
                    if event_booking_result == "PASS" and event_booking_catalog:
                        event_bookingcatalog = json.loads(event_booking_catalog.content)
                        for item in event_bookingcatalog:
                            if item['scheduleInstance'] == contentid_list[0]:
                                uri = item['uri'] 
                        if uri:  
                            print "\n\n###STEP4: Set the 'recordingsToKeep':5 using 'PUT' method with the {item}/recurrence/recordingsToKeep \n"
                            recordingstokeep_value = 5     
                            modify_result = modify_recordingstokeep(protocol,pps_host,pps_port,householdid,recordingstokeep_value,timeout,uri,printflg)
                            if modify_result == "PASS" :
                                print "RecordingsToKeep value modified succesfully" 
                                wait_till_start_time = get_timedifference(
                                    startTime_list[0], printflg)
                                print "Script will wait for ", wait_till_start_time, "Seconds for program to start and ", booked_to_recording_delay, "seconds for state change from Booked to recording"
                                time.sleep(wait_till_start_time +
                                           booked_to_recording_delay)
                                time.sleep(30)
                                record_result, record_responce = record_and_verify(pps_port, protocol, pps_host, householdid, contentid_list[
                                                                                   0], contentid_list, endTime_list, recording_to_recorded_delay,recordingstokeep_value, timeout, printflg)
                            else:   
                                message = "Testcase Failed: RecordingsToKeep value was not modified succesfully"
                                tims_dict = update_tims_data(
                                    tims_dict, 1, event_booking_catalog, ["TC865"])
                                return tims_dict                     
                    else:
                        tims_dict = update_tims_data(
                            tims_dict, 1, event_booking_catalog, ["TC865"])
                        return tims_dict

                    if record_result == "PASS" and record_responce:                       
                        message = "Testcase Passed: Episodes corresponding to set recordingsToKeep value are in RECORDED state and rest stand deleted from the catalog"
                        print message
                        tims_dict = update_tims_data(
                            tims_dict, 0, message, ["TC865"])
                        return tims_dict
                    else:
                        print record_responce 
                        tims_dict = update_tims_data(
                            tims_dict, 1, record_responce, ["TC865"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Error in getting Grid responce"
                    print message
                    tims_dict = update_tims_data(
                        tims_dict, 1, message, ["TC865"])
                    return tims_dict
            except:
                message = "error occured in script\n" + PrintException(True)
                print message
                tims_dict = update_tims_data(
                    tims_dict, 1, message, ["TC865"])
                return tims_dict

def book_and_verify(pps_port, protocol, pps_host, householdid, pps_headers, payload, contentid, contentid_list, catalog_fetch_delay, timeout):
    try:
        result = do_PPSbooking(pps_port, protocol, pps_host,
                               householdid, pps_headers, payload, contentid, timeout)
        if result == "PASS":
            print "PPS Booking completed successfully"
            time.sleep(catalog_fetch_delay)
            print "\n\n###STEP3: Verify the Booked Catalog and see all 6 Episodes are in Booked State \n"
            time.sleep(30)
            verify_book, responce = verify_booking(
                pps_port, protocol, pps_host, householdid, contentid_list, timeout)
            if verify_book == 'PASS':
                return ("PASS", responce)
            else:
                message = "Testcase Failed: BOOKED state could not be verified"
                print message
                return ("FAIL", message)
        else:
            message = "Testcase Failed: PPS Booking failed "
            print message
            return ("FAIL", message)
    except:
        message = "Testcase Failed: Error occured\n " + PrintException(True)
        print message
        return ("FAIL", message)

def record_and_verify(pps_port, protocol, pps_host, householdid, content_id, content_id_list, endTime, recording_to_recorded_delay,recordingtokeep_value, timeout, printflg):
    try:
        print "\n\n###STEP5: Verify the first episode in Recording State and wait till 5 Episodes completes recording \n"
        result_recording, responce_recording = verify_recording_state(
            pps_port, protocol, pps_host, householdid, content_id, timeout)
        if result_recording == "PASS":
            program_end_waittime = get_timedifference(
                (endTime[-2]), printflg)
            print "script will wait for ", str(program_end_waittime), " seconds for recording to complete"
            time.sleep(program_end_waittime)
            time.sleep(30)
        else:
            print "Testcase Failed: Could not Verify RECORDING state "
            message = responce_recording
            return ("FAIL", message)
        time.sleep(recording_to_recorded_delay)
        first_episode_id = content_id_list[0] 
        sixth_episode_id = content_id_list[-1]
        content_without_last_episode = content_id_list
        list_without_last_episode = content_without_last_episode.pop()  
        result_recorded, responce_recorded = verify_recorded_state(
            pps_port, protocol, pps_host, householdid,content_without_last_episode, timeout)
        print "\n\n###STEP6:Verify the Recorded Library and see all 5 Episodes are in Recorded State. Get the contentId of Episode#1 which is oldest \n"
        if result_recorded == "FAIL":
            message = "Testcase Failed: All the episodes which were supposed to be deleted, were not deleted"
            return ("FAIL", message)
        else:
            print "All the episodes(first five episode) are recorded successfully and present in the recording catalog " 
            program_end_waittime = get_timedifference((endTime[-1]), printflg)
            print "script will wait for ", str(program_end_waittime), " seconds for recording to complete"
            time.sleep(program_end_waittime)
            time.sleep(recording_to_recorded_delay)
        print "\n\n###STEP7:Wait till 6th Episode completes recording and verify Episode#1 is not in recorded library and Episode#6 is in the recorded library \n"
        result_recorded, responce_recorded = verify_recorded_state(
            pps_port, protocol, pps_host, householdid, sixth_episode_id, timeout)
        if result_recorded == "PASS":
            print "sixth spisode is present in the recorded catalog"
        else:
            message = "Testcase Failed: Could not verify RECORDED state"
            return ("FAIL", message)
        result_recorded, responce_recorded = verify_recorded_state(
            pps_port, protocol, pps_host, householdid, first_episode_id, timeout)
        if result_recorded == "FAIL":
            message =  "Testcase passed:first episode is not present in the recorded catalog"
            return ("PASS", message)
        else:
            message = "Testcase failed : first episode is still present in the catalog "
            return ("FAIL", message)
    except:
        message = "Testcase Failed: Error occured\n " + PrintException(True)
        return ("FAIL", message)

if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    # read config file
    sa = sys.argv
    cfg = relative_config_file(sa, scriptName)
    if cfg['basic_feature']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
        print
    L = doit_wrapper(cfg, True)
    status_value = []
    for key, val in dict.items(L):
        status_value.append(val[2])
    if status_value:
        if (1 in status_value) or (3 in status_value):
            exit(1)
        else:
            exit(0)
    else:
        exit(1)
