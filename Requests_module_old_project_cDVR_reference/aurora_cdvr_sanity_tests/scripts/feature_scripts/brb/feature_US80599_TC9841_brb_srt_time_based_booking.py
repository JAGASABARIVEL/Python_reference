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
import math
import re
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import (
    set_errorlogging, PrintException, epoch2iso,
    get_utc_time_after_n_minutes, relative_config_file
)
from L2commonFunctions import (
    get_content_playbackURI, get_contentid_from_recid_list,
    get_recId_from_contentplaybackURI,
)
from L3commonFunctions import (
    verify_recording_state, updatetimsresultsjson,
    update_tims_data, cleanup_household,
    fetch_gridRequest, get_contentIddict_bytitle,
    do_PPSbooking, verify_booking, check_time_based_book,
    get_vmr_response, do_PPSbooking_TBR,
    debug_print_log, check_time_based_recording,
)
from RRcommonFunctions import ConfigureSRT
from genChannelLineup import *

########################################################################################################################
# TestcaseId TC9841: Big Red Button - SRT with time based booking
# TestcaseSteps:
# Step1: Ingest an event of 10 minutes with the posttime of 10 Minutes to the CI Host
# CH1 |--EV1--|
# Step2: Setting the SRT table in such a way to record the contents with unique copy type.
# Step3: Fetching the grid response to collect the ingested content.
# Step4: Book Time Based Booking of the above event on hh-1 and hh-2 for first 3 minutes.
# Step5: Confirming that hh-1 and hh-2 households has the EV1 in booked state.
# Step6: Confirming that hh-1 and hh-2 households has the EV1 in recording state.
# Step7: Confirming that the copy type of the recording in hh-1 and hh-2 is unique copy.
# Step8: Setting the SRT table in such a way to record the contents with common copy type.
# Step9: Book Time Based Booking of the above event on hh-3 and hh-4 for last 3 minutes.
# Step10: Confirming that hh-3 and hh-4 households has the EV1 in booked state.
# Step11: Confirming that hh-3 and hh-4 households has the EV1 in recording state.
# Step12: Confirming that the copy type of the recording in hh-3 and hh-4 is common copy.
########################################################################################################################


def doit(cfg, printflg=False):
    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        updatevalue = updatetimsresultsjson(cfg, start_time, end_time, rc, 'feature')
        return updatevalue
    except:
        print "Error Occurred in Script \n"
        PrintException()
        return 1

def doit_wrapper(cfg, printflg=False):

    message = ""
    status = 3
    test_id = "TC9841"
    tims_dict = {test_id: ["US80599", message, status]}
    print "%s: Big Red Button - SRT with time based booking" % test_id

    try:
        # announce
        # abspath = os.path.abspath(__file__)
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
        serviceIdlist.append(unicode(testchannel1))

        prefix = cfg['feature']['household_prefix']
        bookingCatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        recordingstatecheck_timedelay = cfg['pps']['booked_to_recording_delay']
        recording_to_recorded_delay = cfg['pps']['recording_to_recorded_delay']
        householdid1 = prefix + '1'
        householdid2 = prefix + '2'
        householdid3 = prefix + '3'
        householdid4 = prefix + '4'
        householdid_list = [householdid1, householdid2, householdid3, householdid4]
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts))
        broadcasting_starttime = 0
        broadcasting_endtime = 0
        recording_delay = 60
        common_copy = "COMMON"
        unique_copy = "UNIQUE"
        source_region = cfg["recorderRegion"]
        dest_region = cfg["recorderRegion"]
        copy_type = unique_copy
        ingest_delay = 120

        srt_content1 = [[source_region, str(testchannel1), dest_region, "unique"]]
        srt_content2 = [[source_region, str(testchannel1), dest_region, "common"]]
        srt_content_reset = [[source_region, "*", dest_region, "NoChange"]]

        # Do PPS Booking
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        ###########################  USER DEFINED POST TIME IN UTC ############################
        start_delay = 5
        timeslotinminutes = cfg["test_channels"]["xlongProgramLength"]
        ingestion_time = get_utc_time_after_n_minutes(start_delay, True)
        start_time = datetime.datetime.strptime(ingestion_time, '%Y-%m-%dT%H:%M:%S')
        post_time = calendar.timegm(start_time.timetuple()) + 0.0001
        #######################################################################################

        print "\n[STEP1]: Ingest 1 event of n minutes in 3 channels with the posttime of n Minutes to the CI Host"
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']

        eventtitle1 = "uniquecp" + str(random.randint(1, 499))

        channel1 = ChannelLineup(BoundaryInMinutes=0)
        channel1.add_to_lineup(serviceId=testchannel1, timeSlotLengthMinutes=timeslotinminutes,
                               timeSlotCount=1, programIDPrefix=eventtitle1)
        channel1.postXmlData(ci_host, ci_port, startTime=post_time)
        channel1.writeXmlFiles(startTime=post_time)

        print "channel1 : ", channel1

        print "Wait time for the catalog ingest to get synced with the CI Host in seconds: " + str(ingest_delay)
        time.sleep(ingest_delay)
    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
        return tims_dict

    try:
        for (cmdc_host, pps_host) in hostlist:
            try:
                print "\n[STEP2]: Setting the SRT table in such a way to record the contents with unique copy type."
                configureSRT_instance = ConfigureSRT()
                configureSRT_instance.modify_srt(cfg, srt_content1)

                for householdid in householdid_list:
                    cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)

                print "\n[STEP3]: Fetching the grid response to collect the ingested content."
                gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host, cmdc_port, serviceIdlist,
                                                            region, timeout, printflg)
                assert gridservicelistresponse, "Testcase Failed: Unable to Fetch Grid Response"

                contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse, eventtitle1, ['title'])
                print "ContentID dictionary from the Grid Response\n" + str(contentId_dict_all)
                assert contentId_dict_all, "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"

                contentId_list = sorted(contentId_dict_all.items(), key=lambda x: x[1])
                print "ContentId list after Sorting\n" + str(contentId_list)
                assert (
                len(contentId_list) > 0), "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                print "len(contentId_list) : ", len(contentId_list)

                content_ev1 = contentId_list[0][0]

                print "\n[STEP4]: PPS time based booking of the above event on hh-1 and hh-2 for first 3 minutes"
                starttimeinepoch = (int(math.ceil(post_time / 60.0)) * 60)
                endtimeinepoch = starttimeinepoch + (3 * 60)
                programstarttimeiniso = epoch2iso(starttimeinepoch)
                programendtimeiniso = epoch2iso(endtimeinepoch)
                payload = """{
                    "startTime": "%s",
                    "endTime": "%s",
                    "channel": "%d",
                    "checkConflicts" : true,
                    "pvr":"nPVR"
                    }
                    """ % (programstarttimeiniso, programendtimeiniso, testchannel1)

                for household in householdid_list[:2]:
                    print"\nManual booking is Doing for householdId %s : " % household
                    result = do_PPSbooking_TBR(pps_port, protocol, pps_host, household, pps_headers, payload, timeout, printflg=False)
                    if result == "PASS":
                        print "Time Based booking successful for household: ", household
                    else:
                        message = "Testcase Failed: Time Based or Manual Booking failed for the channel %s" % testchannel1
                        print message
                        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
                        return tims_dict

                print "\n[STEP5]: Confirming that hh-1 and hh-2 households has the booked item-1 in booked state."
                time.sleep(bookingCatalog_delay)
                # Getting Catalog Response for the Booked Catalog
                household_contentURI = []
                for householdid in householdid_list[:2]:
                    result_book, message, contentURI, pgm_start_waiTime, booked_catalog, contentPlaybackURI = \
                        check_time_based_book(pps_port, protocol, pps_host, householdid, timeout, programstarttimeiniso,
                                              starttimeinepoch, printflg, contentPlaybackURI=True)
                    contentpalybackuri = (householdid, contentPlaybackURI)
                    household_contentURI.append(contentpalybackuri)
                    if result_book == "PASS" and booked_catalog:
                        print "Time based booking is present in the booking catalog for %s household" % householdid
                    else:
                        message = "Testcase Failed: " + message
                        debug_print_log(pps_port, protocol, pps_host, householdid, timeout)
                        cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
                        return tims_dict
                time.sleep(pgm_start_waiTime)
                time.sleep(recordingstatecheck_timedelay)

                print "\n[STEP6]: Confirming that hh-1 and hh-2 households has the booked item-1 in recording state."
                for householdid in householdid_list[:2]:
                    result_recording, message, pgm_end_waiTime, recording_catalog = \
                        check_time_based_recording(pps_port, protocol, pps_host, householdid, timeout,
                                                   programstarttimeiniso, endtimeinepoch, printflg)
                    if result_recording == "PASS":
                        print "Script will wait for " + str(pgm_end_waiTime / 60) + \
                              " minutes to complete the recording by adding the delay for the state change"
                    else:
                        message = "Testcase Failed: " + message
                        debug_print_log(pps_port, protocol, pps_host, householdid, timeout)
                        cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
                        return tims_dict

                print "\n[STEP7]: Confirming that the copy type of the recording in hh-1 and hh-2 is unique copy."
                playbackuri_list = []
                for uri in household_contentURI:
                    uri_data = str(uri[1])
                    rec_id = (re.search('recId=*([^\n\r]*)', uri_data)).group(1)
                    if rec_id:
                        playbackuri_list.append(str(rec_id))
                print "Playback URI list :", playbackuri_list
                contentidlist = get_contentid_from_recid_list(cfg, playbackuri_list, timeout)
                print "ContentId list :", contentidlist
                vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
                vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
                riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
                riodev_recording_hh2 = json.loads(vmr_response_2.content)[0]
                assert riodev_recording_hh1["CopyType"] == copy_type and riodev_recording_hh2["CopyType"] == copy_type,\
                    "Testcase Failed: Content %s are not in expected copy type %s in " \
                    "household 1 & household 2" % (content_ev1, copy_type)

                print "\n[STEP8]: Setting the SRT table in such a way to record the contents with common copy type."
                configureSRT_instance = ConfigureSRT()
                configureSRT_instance.modify_srt(cfg, srt_content2)

                print "\n[STEP9]: PPS time based booking of the above event on hh-3 and hh-4 for last 3 minutes"
                booking2_start_time = post_time + (6 * 60)
                starttimeinepoch = (int(math.ceil(booking2_start_time / 60.0)) * 60)
                endtimeinepoch = starttimeinepoch + (3 * 60)
                programstarttimeiniso = epoch2iso(starttimeinepoch)
                programendtimeiniso = epoch2iso(endtimeinepoch)
                payload = """{
                                    "startTime": "%s",
                                    "endTime": "%s",
                                    "channel": "%d",
                                    "checkConflicts" : true,
                                    "pvr":"nPVR"
                                    }
                                    """ % (programstarttimeiniso, programendtimeiniso, testchannel1)

                for household in householdid_list[2:4]:
                    print"\nManual booking is Doing for householdId %s : " % household
                    result = do_PPSbooking_TBR(pps_port, protocol, pps_host, household, pps_headers, payload, timeout,
                                               printflg=False)
                    if result == "PASS":
                        print "Time Based booking successful for household: ", household
                    else:
                        message = "Testcase Failed: Time Based or Manual Booking failed for the channel %s" % testchannel1
                        print message
                        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
                        return tims_dict

                print "\n[STEP10]: Confirming that hh-3 and hh-4 households has the booked item-1 in booked state."
                time.sleep(bookingCatalog_delay)
                household_contentURI = []
                # Getting Catalog Response for the Booked Catalog
                for householdid in householdid_list[2:4]:
                    result_book, message, contentURI, pgm_start_waiTime, booked_catalog, contentPlaybackURI = \
                        check_time_based_book(pps_port, protocol, pps_host, householdid, timeout, programstarttimeiniso,
                                              starttimeinepoch, printflg, contentPlaybackURI=True)
                    contentpalybackuri = (householdid, contentPlaybackURI)
                    household_contentURI.append(contentpalybackuri)
                    if result_book == "PASS" and booked_catalog:
                        print "Time based booking is present in the booking catalog for %s household" % householdid
                    else:
                        message = "Testcase Failed: " + message
                        debug_print_log(pps_port, protocol, pps_host, householdid, timeout)
                        cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
                        return tims_dict
                time.sleep(pgm_start_waiTime)
                time.sleep(recordingstatecheck_timedelay)

                print "\n[STEP11]: Confirming that hh-3 and hh-4 households has the booked item-1 in recording state."
                for householdid in householdid_list[2:4]:
                    result_recording, message, pgm_end_waiTime, recording_catalog = \
                        check_time_based_recording(pps_port, protocol, pps_host, householdid, timeout,
                                                   programstarttimeiniso, endtimeinepoch, printflg)
                    if result_recording == "PASS":
                        print "Script will wait for " + str(pgm_end_waiTime / 60) + \
                              " minutes to complete the recording by adding the delay for the state change"
                    else:
                        message = "Testcase Failed: " + message
                        debug_print_log(pps_port, protocol, pps_host, householdid, timeout)
                        cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
                        return tims_dict

                print "\n[STEP12]: Confirming that the copy type of the recording in hh-3 and hh-4 is common copy."
                playbackuri_list = []
                for uri in household_contentURI:
                    uri_data = str(uri[1])
                    rec_id = (re.search('recId=*([^\n\r]*)', uri_data)).group(1)
                    if rec_id:
                        playbackuri_list.append(str(rec_id))
                print "Playback URI list :", playbackuri_list
                contentidlist = get_contentid_from_recid_list(cfg, playbackuri_list, timeout)
                print "ContentId list :", contentidlist
                vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
                vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
                riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
                riodev_recording_hh3 = json.loads(vmr_response_2.content)[0]
                assert riodev_recording_hh1["CopyType"] == common_copy and \
                       riodev_recording_hh3["CopyType"] == common_copy, \
                    "Testcase Failed: Content %s are not in expected copy type %s in " \
                    "household 3 & household 4" % (content_ev1, common_copy)
                message = "Testcase Passed: copy type of the recording in hh-3 and hh-4 is common copy"
                tims_dict = update_tims_data(tims_dict, 0, message, [test_id])

            except AssertionError as ae:
                message = str(ae)
                tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

            except Exception as e:
                message = str(e)
                tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

    except AssertionError as ae:
        message = str(ae)
        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

    except Exception as e:
        message = str(e)
        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

    finally:
        for householdid in householdid_list:
            cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)
        configureSRT_instance = ConfigureSRT()
        configureSRT_instance.modify_srt(cfg, srt_content_reset)
        print message
        return tims_dict


def timeDiff(timestamp):
    diff = ((timestamp/1000) - time.time())
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
    L = doit(cfg, True)
    exit(L)
