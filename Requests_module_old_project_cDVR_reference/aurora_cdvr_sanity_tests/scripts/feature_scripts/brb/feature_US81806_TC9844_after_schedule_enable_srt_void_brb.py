"""
    TC9844: Big Red Button - After Schedule Enable SRT should affect the recording
"""

import os
import sys
import json
import time
import requests
import calendar
import itertools
import datetime
import mypaths
import random

from pprint import pprint
from multiprocessing import Process, Queue
from os.path import isfile
from scripts.lib.readYamlConfig import readYAMLConfigs
from scripts.lib.jsonReadWrite import JsonReadWrite
from genChannelLineup import ChannelLineup
from scripts.lib.L1commonFunctions import (
    set_errorlogging, PrintException, relative_config_file,
    get_timedifference)
from scripts.lib.L2commonFunctions import (
    fetch_bookingCatalog, get_start_and_end_time, get_content_playbackURI,
    get_contentid_from_recid)
from scripts.lib.L3commonFunctions import (
    updatetimsresultsjson, update_tims_data, cleanup_household, fetch_gridRequest,
    get_contentIddict_bytitle, do_PPSbooking, verify_recording_state,
    verify_recorded_state, do_PPSbooking_returnresponse, get_vmr_response)
from scripts.lib.RRcommonFunctions import ConfigureSRT

TESTCASE_STEPS = """
##########################################################################################
# TC9844: Big Red Button - After Schedule Enable SRT should affect the recording
# STEP1: Ingest a event in channel1 with the post time of 25 minutes
# STEP2: Set SRT good known configuration as unique copy.
# STEP3: Disable SRT from RR UI.
# STEP4: Book unique copy event in channel 1 from 3 households and verify booking successful
# STEP5: Wait till event is scheduled, Update SRT configuration as common copy
# STEP6: Enable SRT from RR UI.
# STEP7: Using Playback API verify recording content for all household is
         unique copy type.
# STEP8: Revert Back planner and SRT to its previous state
##########################################################################################
"""

print TESTCASE_STEPS


def doit(cfg, printflg=False):
    """
        The function which actually invokes the test case
    """

    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        update_value = updatetimsresultsjson(
            cfg, start_time, end_time, rc, 'feature')
        return update_value
    except:
        print "Error Occurred in script \n"
        PrintException()
        return 1

def doit_wrapper(cfg, printflg=False):
    """
    Core Functionality of Testcase start with this function
    """

    message = ""
    status = 3
    testcase_id = "TC9844"
    userstory_id = "US81806"
    tims_dict = {
        testcase_id: [userstory_id, message, status],
    }

    try:
        # announce
        script_name = os.path.basename(__file__)
        (test, ext) = os.path.splitext(script_name)
        print "Starting test " + test

        if "no_brb" in cfg["test-flags"]:
            message = "Testcase Skipped: Skipping the testcases since no_brb flag is enabled."
            print message
            tims_dict = update_tims_data(tims_dict, 2, message, [testcase_id])
            return tims_dict

        # Initialize the Variables
        serviceidlist = []
        timeout = 6

        # Channel Details
        # available_channels = cfg['big_red_button']
        available_channels = cfg['cornercase-channelsets']['set1']
        channel1 = cfg['test_channels'][available_channels[0]]['ServiceId']
        serviceidlist.append(unicode(channel1))

        # Planner details
        prefix = cfg['feature']['household_prefix']
        plannerlimit = cfg['feature']['households_needed']
        index = random.randint(0, plannerlimit - 1)
        planner_id = prefix + str(index)

        # Delay
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']
        schedule_delay = 480
        srt_update_delay = 5

        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        householdid1 = prefix + '1'
        householdid2 = prefix + '2'
        householdid3 = prefix + '3'
        householdid_list = [householdid1, householdid2, householdid3]
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts))
        print "hostlist ", hostlist

        print "\n# STEP1: Ingest a event in channel1 with the post time of 25 minutes #\n"
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']

        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        # ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        post_time = time.time() + ingest_minimum_delay + 1500
        print "[INFO: ] post_time ", post_time
        timeslotinminutes = cfg['test_channels']['mediumProgramLength']
        channel = ChannelLineup(BoundaryInMinutes=0)
        eventtitle1 = "random1cp" + str(random.randint(1, 499))
        channel.add_to_lineup(
            serviceId=channel1, timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1, programIDPrefix=eventtitle1)
        channel.postXmlData(ci_host, ci_port, startTime=post_time)
        channel.writeXmlFiles(startTime=post_time)
        length = channel.getTotalLength()
        print "length ", length
        print channel
        time.sleep(ingest_minimum_delay)

    except:
        message = (
            "Test Case Failed: Error Occurred in configuration {0}".format(
                PrintException(True)))
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, [testcase_id])
        return tims_dict

    try:
        # Do PPS Booking
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        pps_port = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']

        cmdc_host = hostlist[0][0]
        pps_host = hostlist[0][1]

        rec_region = cfg['recorderRegion']
        reg_src = cfg['recorderRegion']
        reg_dest = cfg['recorderRegion']
        res_copy_type = "NoChange"

        print "\n# STEP2: Set SRT good known configuration as unique copy. #\n"
        configureSRT_instance = ConfigureSRT()
        configureSRT_instance.set_srt_availability(cfg)
        configureSRT_instance.modify_srt(cfg, [[rec_region, str(channel1), rec_region, "unique"]])

        print "\n# STEP3: Disable SRT from RR UI. #\n"
        time.sleep(srt_update_delay)
        configureSRT_instance.set_srt_availability(cfg, state="Disable")

        for householdid in householdid_list:
            cleanup_household(
                cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)

        grid_response = fetch_gridRequest(
            catalogueId, protocol, cmdc_host, port_cmdc, serviceidlist,
            region, timeout, printflg=False)
        message = "Unable to fetch grid response"
        assert grid_response, message

        evts_content_id_list = []
        start_time_list = []
        end_time_list = []
        if grid_response:
            print grid_response.content
            cont_id_dict_chl1 = get_contentIddict_bytitle(grid_response,eventtitle1,['title'])
            print "cont_id_dict_chl1 ", cont_id_dict_chl1
            if cont_id_dict_chl1:
                event_cont_id_list_ch1 = sorted(cont_id_dict_chl1.items(), key=lambda x:x[1])
                print "event_cont_id_list_ch1 ", event_cont_id_list_ch1
                if event_cont_id_list_ch1:
                    ev1_content_id = event_cont_id_list_ch1[0][0]
                    start_time_list.append(event_cont_id_list_ch1[0][1][0])
                    end_time_list.append(event_cont_id_list_ch1[0][1][1])
                    evts_content_id_list.append(ev1_content_id)
                    payload1 =  """{
                       "checkConflicts": true,
                       "pvr": "nPVR",
                       "scheduleInstanceId": "%s"
                       }"""%(ev1_content_id)

        print (
            "\n# STEP4: Book unique copy event in channel 1 from 3 households and"
            " verify booking successful #\n")
        result, response = do_PPSbooking_returnresponse(
            pps_port, protocol, pps_host, householdid1, pps_headers, payload1,
            evts_content_id_list[0], timeout, printflg)
        message = "Unable to verify PPS booking"
        assert result == "PASS", message
        print "response ", response
        print "result ", result
        print "response content ", response.content
        bookedcatalogresponse = fetch_bookingCatalog(
            pps_port, protocol, pps_host, householdid1, timeout)
        message = "Unable to verify booking catalog"
        assert bookedcatalogresponse, message
        print "bookedcatalogresponse ", bookedcatalogresponse
        print "content ", bookedcatalogresponse.content

        result, response = do_PPSbooking_returnresponse(
            pps_port, protocol, pps_host, householdid2, pps_headers, payload1,
            evts_content_id_list[0], timeout, printflg)
        print "response ", response
        print "result ", result
        print "response content ", response.content
        bookedcatalogresponse = fetch_bookingCatalog(
            pps_port, protocol, pps_host, householdid2, timeout)
        message = "Unable to verify booking catalog"
        assert bookedcatalogresponse, message
        print "bookedcatalogresponse ", bookedcatalogresponse
        print "content ", bookedcatalogresponse.content

        result, response = do_PPSbooking_returnresponse(
            pps_port, protocol, pps_host, householdid3, pps_headers, payload1,
            evts_content_id_list[0], timeout, printflg)
        print "response ", response
        print "result ", result
        print "response content ", response.content
        bookedcatalogresponse = fetch_bookingCatalog(
            pps_port, protocol, pps_host, householdid3, timeout)
        message = "Unable to verify booking catalog"
        assert bookedcatalogresponse, message
        print "bookedcatalogresponse ", bookedcatalogresponse
        print "content ", bookedcatalogresponse.content

        print (
            "\n# STEP5: Wait till event is scheduled,"
            " Update SRT configuration as common copy  #\n")
        time.sleep(schedule_delay)
        configureSRT_instance.modify_srt(cfg, [[rec_region, str(channel1), rec_region, "common"]])

        print "\n# STEP6: Enable SRT from RR UI. #\n"
        time.sleep(srt_update_delay)
        configureSRT_instance.set_srt_availability(cfg)

        print (
            "\n# STEP7: Using Playback API verify recording content for"
            " all household is unique copy type. #\n")

        program_strttime1 = get_timedifference(start_time_list[0], printflg)
        time.sleep(program_strttime1)
        time.sleep(recordingstatecheck_waittime)

        result, resp = verify_recording_state(
            pps_port, protocol, pps_host, householdid1,
            evts_content_id_list[0], timeout)
        message = "Unable to verify recording catalog"
        assert result == "PASS", message
        print "result ", result
        print "resp ", resp
        print "resp content ", resp.content

        for householdid in householdid_list:
            playbackuri_list = get_content_playbackURI(
                pps_host, pps_port, protocol, [evts_content_id_list[0],], [householdid,], timeout)
            print "Playback URI list :", playbackuri_list
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            print "ContentId list :", contentidlist
            vmr_response = get_vmr_response(cfg,contentidlist[0], timeout)
            jsonresponse = json.loads(vmr_response.content)
            print "JSON response :", vmr_response.content
            # VMR Response picked for only one content Id
            # Directly picking the first response content
            resp_dict = jsonresponse[0]
            message = "Unexpectedly! CopyType Still Remains in Unique"
            assert resp_dict["CopyType"] == "UNIQUE", message

        message = "Testcase Passed: After scheduling SRT update wont affect the recording"
        tims_dict = update_tims_data(tims_dict, 0, message, [testcase_id])

    except AssertionError as ae:
        message = "Test case Failed:" + str(ae)
        tims_dict = update_tims_data(tims_dict, 1, message, [testcase_id])
        # debug_print(cfg, planner_id)

    except Exception as e:
        message = "Test case Failed: " + str(e)
        tims_dict = update_tims_data(tims_dict, 1, message, [testcase_id])
        # debug_print(cfg, planner_id)

    finally:
        # cleanup_planner(cfg, planner_id)
        for householdid in householdid_list:
            cleanup_household(
                cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)
        configureSRT_instance = ConfigureSRT()
        configureSRT_instance.modify_srt(
            cfg, [[reg_src, "*", reg_dest, res_copy_type]])
        print message
        return tims_dict

if __name__ == '__main__':
    script_name = os.path.basename(__file__)
    # read config file
    sa = sys.argv
    cfg = relative_config_file(sa, script_name)
    if cfg['feature']['print_cfg']:
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
