"""
    TC9587: Big Red Button - static_routing_table.txt file edited - change sourceRegion to *
"""

import os
import sys
import json
import time
# import requests
# import calendar
import itertools
# import datetime
from pprint import pprint
import random
import mypaths

# from multiprocessing import Process, Queue
# from os.path import isfile
# from scripts.lib.readYamlConfig import readYAMLConfigs
# from scripts.lib.jsonReadWrite import JsonReadWrite
from genChannelLineup import ChannelLineup
from scripts.lib.L1commonFunctions import (
    set_errorlogging, PrintException, relative_config_file,
    get_timedifference, get_hosts_by_config_type)
from scripts.lib.L2commonFunctions import (
    fetch_bookingCatalog, get_content_playbackURI,
    get_contentid_from_recid)
from scripts.lib.L3commonFunctions import (
    updatetimsresultsjson, update_tims_data, cleanup_household, fetch_gridRequest,
    get_contentIddict_bytitle, verify_recording_state,
    do_PPSbooking_returnresponse, get_vmr_response)
from scripts.lib.RRcommonFunctions import ConfigureSRT
from basic_create_household import _create_household

TESTCASE_STEPS = """
#########################################################################################
# TC9587: Big Red Button - static_routing_table.txt file edited
#         - change sourceRegion to *
#########################################################################################
# STEP1: Login into RR and update the static_route_table to record
         sourceRegion to *
# STEP2: Get List of Recording Region and create households with those regions
# STEP3: Book a program for 2 minutes in all the households
# STEP4: Check weather the recording happens in same destinationRegion.
#########################################################################################
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
            cfg, start_time, end_time, rc, 'big_red_button')
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
    testcase_id = "TC9587"
    userstory_id = "US79253"
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

        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]

        #householdid1 = prefix + '1'
        #householdid2 = prefix + '2'
        #householdid_list = [householdid1, householdid2]
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts))
        print "hostlist ", hostlist

        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']

        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        # ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        post_time = time.time() + ingest_minimum_delay + 120
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

        dest_rec_region = cfg['recorderRegion']
        src_rec_region = "*"
        reg_src = cfg['recorderRegion']
        reg_dest = cfg['recorderRegion']
        res_copy_type = "NoChange"

        print (
            "\n# STEP1: Login into RR and update the static_route_table to record"
            " sourceRegion to * #\n")
        configureSRT_instance = ConfigureSRT()
        configureSRT_instance.modify_srt(
            cfg, [[src_rec_region, str(channel1), dest_rec_region, "unique"]])

        print (
            "\n# STEP2: Get List of Recording Region and create households"
            " with those regions #\n")
        #for householdid in householdid_list:
        #    cleanup_household(
        #        cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)

        rr_res, rr_res_cont = configureSRT_instance.get_rr_regions_list(cfg)
        message = "Unable to Fetch RR regions list"
        assert rr_res, message

        reg_list = []
        # rr_res_cont = json.loads(resp.content)
        for regn in rr_res_cont:
            reg_list.append(regn['region'])

        hosts = get_hosts_by_config_type(cfg, 'upm', printflg)
        print "[INFO: ] hosts ", hosts
        # inx_list = []
        householdid_list = []
        for host in hosts:
            for index, regn in enumerate(reg_list):
                print "[INFO: ] index ", index
                print "[INFO: ] regn ", regn
                inx_prefix = "tc9587" + str(index)
                householdid_list.append(prefix + inx_prefix)
                res_status = _create_household(inx_prefix, host, cfg, regn, prefix)
                print "[INFO: ] res_status ", res_status

        time.sleep(5)
        householdid1 = householdid_list[0]
        householdid2 = householdid_list[1]
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
            cont_id_dict_chl1 = get_contentIddict_bytitle(grid_response, eventtitle1, ['title'])
            print "cont_id_dict_chl1 ", cont_id_dict_chl1
            if cont_id_dict_chl1:
                event_cont_id_list_ch1 = sorted(cont_id_dict_chl1.items(), key=lambda x:x[1])
                print "event_cont_id_list_ch1 ", event_cont_id_list_ch1
                if event_cont_id_list_ch1:
                    ev1_content_id = event_cont_id_list_ch1[0][0]
                    start_time_list.append(event_cont_id_list_ch1[0][1][0])
                    end_time_list.append(event_cont_id_list_ch1[0][1][1])
                    evts_content_id_list.append(ev1_content_id)
                    payload1 = """{
                       "checkConflicts": true,
                       "pvr": "nPVR",
                       "scheduleInstanceId": "%s"
                       }"""%(ev1_content_id)

        print "\n# STEP3: Book a program for 2 minutes (unique copy) in all the households #\n"
        print "[INFO: ] householdid1 ", householdid1
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

        print (
            "\n# STEP4: Check weather the recording happens successfully or not and then check"
            " the recording type (fanout value), it should to common copy #\n")
        program_strttime1 = get_timedifference(start_time_list[0], printflg)
        print "[INFO: ] recording check wait time ", program_strttime1
        time.sleep(program_strttime1)
        time.sleep(recordingstatecheck_waittime + 50)

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
            vmr_response = get_vmr_response(cfg, contentidlist[0], timeout)
            jsonresponse = json.loads(vmr_response.content)
            print "JSON response :", vmr_response.content
            # VMR Response picked for only one content Id
            # Directly picking the first response content
            resp_dict = jsonresponse[0]
            message = "Unexpectedly! recording region is not same for different households"
            assert resp_dict["A8UpdateURL"].split("/")[-1] == dest_rec_region, message

        message = "Testcase Passed: video recording happened in same recording region"
        tims_dict = update_tims_data(tims_dict, 0, message, [testcase_id])

    except AssertionError as ae:
        message = "Test case Failed:" + str(ae)
        tims_dict = update_tims_data(tims_dict, 1, message, [testcase_id])

    except Exception as e:
        message = "Test case Failed: " + str(e)
        tims_dict = update_tims_data(tims_dict, 1, message, [testcase_id])

    finally:
        # cleanup_planner(cfg, planner_id)
        configureSRT_instance = ConfigureSRT()
        configureSRT_instance.modify_srt(
            cfg, [[reg_src, "*", reg_dest, res_copy_type]])
        for householdid in householdid_list:
            cleanup_household(
                cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)
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
