#!/usr/bin/python
import os
import sys
import json
from pprint import pprint
import time
import calendar
import itertools
import datetime
import random
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import (
    set_errorlogging, PrintException,
    get_utc_time_after_n_minutes, relative_config_file
)
from L2commonFunctions import (
    get_content_playbackURI, get_contentid_from_recid,
)
from L3commonFunctions import (
    verify_recording_state, updatetimsresultsjson,
    update_tims_data, cleanup_household,
    fetch_gridRequest, get_contentIddict_bytitle,
    do_PPSbooking, verify_booking,
    get_vmr_response
)
from RRcommonFunctions import ConfigureSRT
from genChannelLineup import *

##########################################################################
# TestcaseId: TC9586
# Testcase Steps: Big Red Button - static_routing_table.txt file
#                 edited before event SCHEDULE and event RECORD.
# STEP1: Ingest an event of n minutes with the posttime of n Minutes to the CI Host
# STEP2: Fetch the grid response to collect the ingested content.
# STEP3: Perform the PPS event-1 booking for all four households.
# STEP4: Perform the PPS event-2 booking for all four households.
# STEP5: Confirm that all four households has the booked item-1 in booked state.
# STEP6: Confirm that all four households has the booked item-2 in booked state.
# STEP7: Change the SRT file in such a way that to record the upcoming
#        scheduling contents with common copy type.
# STEP8: Confirm that all four households has the booked item-1 in recording state.
# STEP9: Confirm that all households, recording its content-1 with copy type as unique.
# STEP10: Confirm that all four households has the booked item-2 in recording state.
# STEP11: Confirm that all households, recording its content-2 with copy type as common.
##########################################################################


def doit(cfg, printflg=False):
    """
    Callback routine for the engine.
    """
    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        updatevalue = updatetimsresultsjson(
            cfg, start_time, end_time, rc, 'basic-feature')
        return updatevalue
    except BaseException:
        print "Error Occurred in Script \n"
        PrintException()
        return (1)


def doit_wrapper(cfg, printflg=False):
    """
    Entrypoint routine for the TC.
    """
    message = ""
    status = 3
    test_id = "TC9586"
    tims_dict = {test_id: ["US79250", message, status]}
    print "%s: Big Red Button - static_routing_table.txt file " \
           "edited before event SCHEDULE and event RECORD." % (test_id)
    try:
        # announce
        #abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        if "no_brb" in cfg["test-flags"]:
            message = "Testcase Skipped: Skipping the testcases since no_brb flag is enabled."
            print message
            tims_dict = update_tims_data(tims_dict, 2, message, [test_id])
            return tims_dict

        # Initialize the Variables
        timeout = 2
        serviceIdlist = []

        # set values based on config
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        testchannel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        testchannel3 = cfg['test_channels']['GenericCh3']['ServiceId']
        serviceIdlist.append(unicode(testchannel1))
        serviceIdlist.append(unicode(testchannel2))
        serviceIdlist.append(unicode(testchannel3))
        prefix = cfg['feature']['household_prefix']
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        recordingstatecheck_timedelay = cfg['pps']['booked_to_recording_delay']
        householdid1 = prefix + '1'
        householdid2 = prefix + '2'
        householdid3 = prefix + '3'
        householdid4 = prefix + '4'
        householdid_list = [
            householdid1,
            householdid2,
            householdid3,
            householdid4]
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts))

        recording_delay = 60
        ingestion_delay = 120
        common_copy = "COMMON"
        unique_copy = "UNIQUE"
        source_region = cfg["recorderRegion"]
        dest_region = cfg["recorderRegion"]
        srt_content = [[source_region, "*", dest_region, "common"]]
        srt_content_reset = [[source_region, "*", dest_region, "NoChange"], ]

        # Do PPS Booking
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        ###########################  USER DEFINED POST TIME IN UTC ############
        start_delay = 5
        # Duration of the event is more than 20 minutes.This dusration is to avoid
        # the pps to send the schedule request for the event 2 which in turn will
        # help to test the BRB.
        timeslotinminutes = cfg["test_channels"]["longProgramLength"] * 5
        ingestion_time = get_utc_time_after_n_minutes(start_delay, True)
        start_time = datetime.datetime.strptime(
            ingestion_time, '%Y-%m-%dT%H:%M:%S')
        post_time = calendar.timegm(start_time.timetuple()) + 0.0001
        #######################################################################

        print "### STEP1: Ingest an event of n minutes with the " \
              "posttime of n Minutes to the CI Host ######## \n \n"
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        #ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        #ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']

        eventtitle1 = "commoncp" + str(random.randint(1, 499))

        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=testchannel1,
                              timeSlotLengthMinutes=timeslotinminutes,
                              timeSlotCount=2,
                              programIDPrefix=eventtitle1)
        channel.postXmlData(ci_host, ci_port, startTime=post_time)
        channel.writeXmlFiles(startTime=post_time)
        #length = channel.getTotalLength()

        print "Wait time for the catalog ingest to "\
        "get synced with the CI Host in seconds: " + str(ingestion_delay)
        time.sleep(ingestion_delay)

    except BaseException:
        message = "Testcase Failed: Error Occurred in Configuration " + \
            PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
        return tims_dict

    for (cmdc_host, pps_host) in hostlist:
        try:

            # Cleanup HH
            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, pps_host,
                                  householdid, pps_headers, timeout)
            # Setting the SRT table in such a way to record the contents with Unique copy type.
            #configureSRT_instance = ConfigureSRT()
            #configureSRT_instance.modify_srt(cfg, [[source_region, "*", dest_region, "NoChange"]])

            print "### STEP2: Fetching the grid response "\
            "to collect the ingested content. ##### \n \n"
            gridservicelistresponse = fetch_gridRequest(
                catalogueId,
                protocol,
                cmdc_host,
                cmdc_port,
                serviceIdlist,
                region,
                timeout,
                printflg)
            assert gridservicelistresponse, "Testcase Failed: Unable to Fetch Grid Response"

            contentId_dict_all = get_contentIddict_bytitle(
                gridservicelistresponse, eventtitle1, ['title'])
            print "ContentID dictionary from the "\
            "Grid Response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable to\
            Form ContentId dictionary from the Grid Response"

            contentId_list = sorted(
                contentId_dict_all.items(),
                key=lambda x: x[1])
            print "ContentId list after Sorting\n" + str(contentId_list)
            assert (len(contentId_list) > 0), "Testcase Failed: Unable "\
                       "to form ContentId list from ContentId dictionary"

            content_ev1 = contentId_list[0][0]
            content_ev2 = contentId_list[1][0]

            payload_ev1 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev1)

            payload_ev2 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev2)

            print "About to start the event 1 booking\n\n"
            print "### STEP3: PPS event-1 booking is "\
            "being done for all four households. ##### \n \n"
            for householdid in householdid_list:
                result = do_PPSbooking(
                    pps_port,
                    protocol,
                    pps_host,
                    householdid,
                    pps_headers,
                    payload_ev1,
                    content_ev1,
                    timeout,
                    printflg)
                if result != "PASS":
                    message = "Testcase Failed:Unable to do pps booking of content ID " + \
                        str(content_ev1) + " in household " + str(householdid)
                    print message
                    tims_dict = update_tims_data(
                        tims_dict, 1, message, ["TC1699"])
            print "PPS Booking is successful for the event "\
            "contentid ", content_ev1, " on all 4 households"

            print "About to start the event 2 booking on all the four households\n\n"
            print "### STEP4: PPS event-2 booking is being done for all four households. ### \n \n"
            for householdid in householdid_list:
                result = do_PPSbooking(
                    pps_port,
                    protocol,
                    pps_host,
                    householdid,
                    pps_headers,
                    payload_ev2,
                    content_ev2,
                    timeout,
                    printflg)
                if result != "PASS":
                    message = "Testcase Failed:Unable to do pps booking of content ID " + \
                        str(content_ev2) + " in household " + str(householdid)
                    print message
                    tims_dict = update_tims_data(
                        tims_dict, 1, message, ["TC1699"])
            print "PPS Booking is successful for the "\
            "event contentid ", content_ev2, " on all 4 households"
            print "### STEP5: Confirming that all four households "\
            "has the booked item-1 in booked state. ### \n \n"
            time.sleep(fetch_bookingcatalog_delay)
            broadcasting_starttime = 0
            #broadcasting_endtime = 0
            # Getting Catalog Response for the Booked Catalog
            for householdid in householdid_list:
                catalogresult, catalogresponse = verify_booking(
                    pps_port, protocol, pps_host, householdid, content_ev1, timeout)
                print "Booking response :", catalogresult
                if catalogresult == "PASS":
                    jsonresponse = json.loads(catalogresponse.content)
                    for items in jsonresponse:
                        try:
                            if items['scheduleInstance'] == content_ev1:
                                broadcasting_starttime = items['content']['broadcastDateTime']
                                #broadcasting_endtime = items['content']['endAvailability']
                        except BaseException:
                            pass
                else:
                    message = "TestCase  Failed : Content ID " + \
                        str(content_ev1) + " in household " + \
                        str(householdid) + " is not in the BOOKED state"
                    assert False, message

            print "#### STEP6: Confirming that all four households has "\
            "the booked item-2 in booked state. ##### \n \n"
            broadcasting_starttime1 = 0
            #broadcasting_endtime1 = 0
            # Getting Catalog Response for the Booked Catalog
            for householdid in householdid_list:
                catalogresult, catalogresponse = verify_booking(
                    pps_port, protocol, pps_host, householdid, content_ev2, timeout)
                print "Booking response :", catalogresult
                if catalogresult == "PASS":
                    jsonresponse = json.loads(catalogresponse.content)
                    for items in jsonresponse:
                        try:
                            if items['scheduleInstance'] == content_ev2:
                                broadcasting_starttime1 = items['content']['broadcastDateTime']
                                #broadcasting_endtime1 = items['content']['endAvailability']
                        except BaseException:
                            pass
                else:
                    message = "TestCase  Failed : Content ID " + \
                        str(content_ev2) + " in household " + \
                        str(householdid) + " is not in the BOOKED state"
                    assert False, message

            recordingstatechage = recordingstatecheck_timedelay + \
                timeDiff(broadcasting_starttime)
            print "Script will wait for " + str(recordingstatechage / 60) + \
                " minutes to check the event recording state"
            time.sleep(recordingstatechage)
            print "Waiting additional %s seconds to workaround "\
            "the recording state change issue." % (recording_delay)
            time.sleep(recording_delay)

            print "### STEP7: Changing the SRT file in such a way that "\
            "to record the upcoming contents with common copy type. ##### \n \n"
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content)

            print "### STEP8: Confirming that all four households has the "\
            "booked item-1 in recording state. ##### \n \n"
            for householdid in householdid_list:
                recordingcatalogresult = verify_recording_state(
                    pps_port, protocol, pps_host, householdid, content_ev1, timeout)[0]
                print "recordingcatalogresult : ", recordingcatalogresult
                if recordingcatalogresult != "PASS":
                    message = "Testcase Failed: Content ID {0} in "\
                    "household {1} is not in the RECORDING state".format(
                        content_ev1, householdid)
                    assert False, message

            print "### STEP9: Confirming that all households, "\
            "recording its content-1 with copy type as unique. ##### \n \n"
            playbackuri_list = get_content_playbackURI(
                pps_host, pps_port, protocol, [content_ev1], householdid_list, timeout)
            contentidlist = get_contentid_from_recid(
                cfg, playbackuri_list, timeout)

            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
            vmr_response_3 = get_vmr_response(cfg, contentidlist[2], timeout)
            vmr_response_4 = get_vmr_response(cfg, contentidlist[3], timeout)

            riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
            riodev_recording_hh2 = json.loads(vmr_response_2.content)[0]
            riodev_recording_hh3 = json.loads(vmr_response_3.content)[0]
            riodev_recording_hh4 = json.loads(vmr_response_4.content)[0]

            assert riodev_recording_hh1["CopyType"] == unique_copy and \
                riodev_recording_hh2["CopyType"] == unique_copy and \
                riodev_recording_hh3["CopyType"] == unique_copy and \
                riodev_recording_hh4["CopyType"] == unique_copy, \
                "Testcase Failed: Contents are not in unique copy in some households."
            print "Contents are getting recorded in unique copy in all households."

            print "### STEP10: Confirming that all four households "\
            "has the booked item-2 in recording state. ##### \n \n"
            recordingstatechage = recordingstatecheck_timedelay + \
                timeDiff(broadcasting_starttime1)
            print "Script will wait for " + str(recordingstatechage / 60)\
                + " minutes to check the event recording state"
            time.sleep(recordingstatechage)

            for householdid in householdid_list:
                recordingcatalogresult = verify_recording_state(
                    pps_port, protocol, pps_host, householdid, content_ev2, timeout)[0]
                if recordingcatalogresult != "PASS":
                    message = "Testcase Failed: Content ID {0} in "\
                    "household {1} is not in the RECORDING state".format(
                        content_ev2, householdid)
                    assert False, message

            print "### STEP11: Confirming that all households, recording "\
            "its content-2 with copy type as common. ##### \n \n"
            playbackuri_list = get_content_playbackURI(
                pps_host, pps_port, protocol, [content_ev2], householdid_list, timeout)
            contentidlist = get_contentid_from_recid(
                cfg, playbackuri_list, timeout)

            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
            vmr_response_3 = get_vmr_response(cfg, contentidlist[2], timeout)
            vmr_response_4 = get_vmr_response(cfg, contentidlist[3], timeout)

            riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
            riodev_recording_hh2 = json.loads(vmr_response_2.content)[0]
            riodev_recording_hh3 = json.loads(vmr_response_3.content)[0]
            riodev_recording_hh4 = json.loads(vmr_response_4.content)[0]

            assert riodev_recording_hh1["CopyType"] == common_copy \
                and riodev_recording_hh2["CopyType"] == common_copy\
                and riodev_recording_hh3["CopyType"] == common_copy\
                and riodev_recording_hh4["CopyType"] == common_copy,\
                "Testcase Failed: Contents are not in common copy in some households."
            print "Contents are getting recorded in common copy in all households."

            message = "TestCase Passed : SRT is working as expected for the "\
            "scenario of changing the copytype before between recording and scheduling."
            tims_dict = update_tims_data(tims_dict, 0, message, [test_id])

        except AssertionError as ae:
            message = str(ae)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        except Exception as e:
            message = str(e)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        finally:
            # Cleanup HH
            for householdid in householdid_list:
                cleanup_household(
                    cfg,
                    pps_port,
                    protocol,
                    pps_host,
                    householdid,
                    pps_headers,
                    timeout)
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content_reset)
            print message
            return tims_dict


def timeDiff(timestamp):
    """
    Provides the timedifference from the current time to recording start
    in seconds with the future standard UTC time as input.
    """
    diff = ((timestamp / 1000) - time.time())
    if diff < 0:
        return 1
    else:
        return diff


if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    # read config file
    sa = sys.argv
    cfg = relative_config_file(sa, scriptName)
    if cfg['feature']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
        print
    L = doit(cfg, True)
    exit(L)
