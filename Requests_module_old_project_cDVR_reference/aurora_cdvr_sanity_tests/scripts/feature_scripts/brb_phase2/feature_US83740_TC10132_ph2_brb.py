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
    get_vmr_response, switch_vmr_host
)
from RRcommonFunctions import ConfigureSRT
from genChannelLineup import *


#########################################################################
# TestcaseId: TC10132
# TestcaseSteps: BRB - Dual VMR - Redirect recording before scheduling from VMR1 to VMR2 for all channels with common copy type.
# STEP 1: Ingest an event on channel 1 & channel 2 with 5 minutes duration and 5 minues post time.
#
#         0     5     10
#         |     |     |
#         |-----|-----|	
#          <--->| CH1
#           POST  CH2
#	        TIME
#
# STEP 2: Ensure four household present in the system pointing to RR1 recording region.
# STEP 3: Modify the SRT in such a way to record the contents from any channel with common copy type in RR2 recording region.
#
#          RR1|*|RR2|Common
#
# STEP 4: Perform booking on all four households for the ingested contents.
#    STEP 4.1: Perform the booking on channel 1 on hh 1 & hh2.
#    STEP 4.2: Perform the booking on channel 2 on hh 3 & hh4.
#
#          HH1 <-----
#                    |--- CH1
#          HH2 <-----
#
#          HH3 <-----
#                    |--- CH2
#          HH4 <-----
#
# STEP 5: Wait for the program to start its recording on all four households.
# STEP 6: Confirm from VMR API response that recorded contents.
#    STEP 6.1: Content from channel 1 recorded on hh1 & hh2 with common copy type in RR2 recording region.
#    STEP 6.1: Content from channel 2 recorded on hh3 & hh4 with common copy type in RR2 recording region.
# STEP 7: Cleanup the households and srt table.
#########################################################################


def doit(cfg, printflg=False):
    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        updatevalue = updatetimsresultsjson(cfg, start_time, end_time, rc, 'basic-feature')
        return updatevalue
    except:
        print  "Error Occurred in Script \n"
        PrintException()
        return (1)


def doit_wrapper(cfg, printflg=False):
    message = ""
    status = 3
    test_id = "TC10132"
    tims_dict = {test_id: ["US80587", message, status]}
    print "%s: BRB - Dual VMR - Redirect recording before scheduling from VMR1 to VMR2 for all channels with common copy type." % (test_id)

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

        ch1 = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["channels"][0]
        ch2 = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["channels"][1]

        testchannel1 = cfg['test_channels'][ch1]['ServiceId']
        testchannel1_uuid = cfg['test_channels'][ch1]['UUID']
        testchannel2 = cfg['test_channels'][ch2]['ServiceId']

        serviceIdlist.append(unicode(testchannel1))
        serviceIdlist.append(unicode(testchannel2))

        prefix = cfg['feature']['household_prefix']
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        recordingstatecheck_timedelay = cfg['pps']['booked_to_recording_delay']
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
        source_region =  cfg["feature"]["brb"]["Recorderegions"]["v2pcVMR"]["name"]
        dest_region =  cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["name"]
        v2pcVMR_host = cfg["vmr"]["instances"]["v2pcVMR"]
        standaloneVMR_host = cfg["vmr"]["instances"]["standaloneVMR"]
        default_copy_type = unique_copy
        ingest_delay = 120

        srt_content = [[source_region, "*", dest_region, "Common"]]
        srt_content_reset = [[source_region, "*", source_region, "NoChange"]]

        # Do PPS Booking
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        ###########################  USER DEFINED POST TIME IN UTC ############################
        start_delay = 5
        timeslotinminutes = cfg["test_channels"]["longProgramLength"]
        ingestion_time = get_utc_time_after_n_minutes(start_delay, True)
        start_time = datetime.datetime.strptime(ingestion_time, '%Y-%m-%dT%H:%M:%S')
        post_time = calendar.timegm(start_time.timetuple()) + 0.0001
        #######################################################################################

        print "### STEP1: Ingest an event of n minutes with the " \
              "posttime of n Minutes to the CI Host ######## \n \n"
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']

        eventtitle1 = "TC10132" + str(random.randint(1, 499))

        channel1 = ChannelLineup(BoundaryInMinutes=0)
        channel1.add_to_lineup(serviceId=testchannel1, \
                               timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=1, \
                               programIDPrefix=eventtitle1)
        channel1.postXmlData(ci_host, ci_port, startTime=post_time)
        channel1.writeXmlFiles(startTime=post_time)

        print "channel1 : ", channel1

        channel2 = ChannelLineup(BoundaryInMinutes=0)
        channel2.add_to_lineup(serviceId=testchannel2, \
                               timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=1, \
                               programIDPrefix=eventtitle1)
        channel2.postXmlData(ci_host, ci_port, startTime=post_time)
        channel2.writeXmlFiles(startTime=post_time)

        print "channel2 : ", channel2

        print "Wait time for the catalog ingest to " \
              "get synced with the CI Host in seconds: " + str(ingest_delay)
        time.sleep(ingest_delay)

    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
        return tims_dict

    for (cmdc_host, pps_host) in hostlist:
        try:

            print "### STEP2: Setting the SRT table. ###### \n \n"
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content)

            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, \
                                  pps_host, householdid, pps_headers, timeout)

            print "### STEP3: Fetching the grid response to " \
                  "collect the ingested content. ##### \n \n"
            gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host, \
                                                        cmdc_port, [unicode(testchannel1),], region, timeout, printflg)
            assert gridservicelistresponse, "Testcase Failed: Unable to Fetch Grid Response"

            contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse, \
                                                           eventtitle1, ['title'])
            print "ContentID dictionary from the Grid Response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable " \
                                       "to Form ContentId dictionary from the Grid Response"

            contentId_list = sorted(contentId_dict_all.items(), key=lambda x: x[1])
            print "ContentId list after Sorting\n" + str(contentId_list)
            assert (len(contentId_list) > 0), "Testcase Failed: Unable " \
                                              "to form ContentId list from ContentId dictionary"
            print "len(contentId_list) : ", len(contentId_list)

            content_ev1 = contentId_list[0][0]


            gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host, \
                                                        cmdc_port, [unicode(testchannel2),], region, timeout, printflg)
            assert gridservicelistresponse, "Testcase Failed: Unable to Fetch Grid Response"

            contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse, \
                                                           eventtitle1, ['title'])
            print "ContentID dictionary from the Grid Response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable " \
                                       "to Form ContentId dictionary from the Grid Response"

            contentId_list = sorted(contentId_dict_all.items(), key=lambda x: x[1])
            print "ContentId list after Sorting\n" + str(contentId_list)
            assert (len(contentId_list) > 0), "Testcase Failed: Unable " \
                                              "to form ContentId list from ContentId dictionary"
            print "len(contentId_list) : ", len(contentId_list)



            content_ev2 = contentId_list[0][0]

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
            print "### STEP4: PPS event-1(on hh1, hh2), event-2(on hh3, hh4) " \
                  "booking respectively from channel 1 & channel 2 is being done. ##### \n \n"
            for householdid in householdid_list[:2]:
                result = do_PPSbooking(pps_port, protocol, pps_host, householdid, \
                                       pps_headers, payload_ev1, content_ev1, timeout, printflg)
                if result != "PASS":
                    message = "Testcase Failed:Unable to do pps booking of content ID " \
                              + str(content_ev1) + " in household " + str(householdid)
                    print message
                    tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

            for householdid in householdid_list[2:4]:
                result = do_PPSbooking(pps_port, protocol, pps_host, householdid, \
                                       pps_headers, payload_ev2, content_ev2, timeout, printflg)
                if result != "PASS":
                    message = "Testcase Failed:Unable to do pps booking of content ID " \
                              + str(content_ev2) + " in household " + str(householdid)
                    print message
                    tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

            print "### STEP5: Confirming that the households has the items " \
                  "in booked state. ##### \n \n"
            time.sleep(fetch_bookingcatalog_delay)
            # Getting Catalog Response for the Booked Catalog
            for householdid in householdid_list[:2]:
                catalogresult, catalogresponse = verify_booking(pps_port, protocol, \
                                                                pps_host, householdid, content_ev1, timeout)
                print "Booking response :", catalogresult
                if catalogresult == "PASS":
                    jsonresponse = json.loads(catalogresponse.content)
                    for items in jsonresponse:
                        try:
                            if items['scheduleInstance'] == content_ev1:
                                broadcasting_starttime = items['content']['broadcastDateTime']
                                broadcasting_endtime = items['content']['endAvailability']
                        except:
                            pass
                else:
                    message = "TestCase  Failed : Content ID " + str(content_ev1) + " in household " \
                              + str(householdid) + " is not in the BOOKED state"
                    assert False, message

            for householdid in householdid_list[2:4]:
                catalogresult, catalogresponse = verify_booking(pps_port, \
                                                                protocol, pps_host, householdid, \
                                                                content_ev2, timeout)
                print "Booking response :", catalogresult
                if catalogresult == "PASS":
                    jsonresponse = json.loads(catalogresponse.content)
                    for items in jsonresponse:
                        try:
                            if items['scheduleInstance'] == content_ev2:
                                broadcasting_starttime = items['content']['broadcastDateTime']
                                broadcasting_endtime = items['content']['endAvailability']
                        except:
                            pass
                else:
                    message = "TestCase  Failed : Content ID " \
                              + str(content_ev2) + " in household " + str(householdid) \
                              + " is not in the BOOKED state"
                    assert False, message


            broadcasting_starttime = timeDiff(broadcasting_starttime)
            recordingstatechage = recordingstatecheck_timedelay + broadcasting_starttime
            print "Script will wait for " + str(recordingstatechage / 60) \
                  + " minutes to check the event recording state"
            time.sleep(recordingstatechage)
            print "Waiting additional %s seconds to workaround the " \
                  "state change issue." % (recording_delay)
            time.sleep(recording_delay)
            time.sleep(recording_delay)

            print "### STEP6: Confirming that all households has the booked items " \
                  "in recording state. ##### \n \n"
            for householdid in householdid_list[:2]:
                recordingcatalogresult, recordingcatalogresponse = verify_recording_state(pps_port, \
                                                                                          protocol, pps_host,
                                                                                          householdid, content_ev1,
                                                                                          timeout)
                if recordingcatalogresult != "PASS":
                    message = "Testcase Failed: Content ID {0} in household {1} is " \
                              "not in the RECORDING state".format(content_ev1, householdid)
                    assert False, message

            for householdid in householdid_list[2:4]:
                recordingcatalogresult, recordingcatalogresponse = verify_recording_state(pps_port, \
                                                                                          protocol, pps_host,
                                                                                          householdid, \
                                                                                          content_ev2, timeout)
                if recordingcatalogresult != "PASS":
                    message = "Testcase Failed: Content ID {0} in household {1} is not in the " \
                              "RECORDING state".format(content_ev2, householdid)
                    assert False, message

            print "### STEP7: Confirming that all households, recording its content " \
                  "with expected copy type and in expected region. ##### \n \n"

            switch_vmr_host(cfg, standaloneVMR_host)
            playbackuri_list = get_content_playbackURI(pps_host, pps_port, \
                                                       protocol, [content_ev1], householdid_list[:2], timeout)
            print "Playback URI list :", playbackuri_list
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            print "ContentId list :", contentidlist
            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
            riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
            riodev_recording_hh2 = json.loads(vmr_response_2.content)[0]

            print "riodev_recording_hh1 : ", riodev_recording_hh1
            print "riodev_recording_hh2 : ", riodev_recording_hh2
            assert riodev_recording_hh1["CopyType"] == common_copy and \
                   riodev_recording_hh2["CopyType"] == common_copy and \
                   riodev_recording_hh1["A8UpdateURL"].split('/')[5] == dest_region and \
                   riodev_recording_hh2["A8UpdateURL"].split('/')[5] == dest_region, \
                "Testcase Failed: Content %s are not in expected copy " \
                "type %s in household 1 & household 2." % (content_ev1, common_copy)

            playbackuri_list = get_content_playbackURI(pps_host, \
                                                       pps_port, protocol, \
                                                       [content_ev2], householdid_list[2:4], timeout)
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
            riodev_recording_hh3 = json.loads(vmr_response_1.content)[0]
            riodev_recording_hh4 = json.loads(vmr_response_2.content)[0]
            print "riodev_recording_hh3 : ", riodev_recording_hh3
            print "riodev_recording_hh4 : ", riodev_recording_hh4
            assert riodev_recording_hh3["CopyType"] == common_copy and \
                   riodev_recording_hh4["CopyType"] == common_copy and \
                   riodev_recording_hh3["A8UpdateURL"].split('/')[5] == dest_region and \
                   riodev_recording_hh4["A8UpdateURL"].split('/')[5] == dest_region, \
                "Testcase Failed: Content %s are not in expected copy " \
                "type %s in household 3 & household 4." % (content_ev2, default_copy_type)

            message = "TestCase Passed : SRT is working as expected."
            tims_dict = update_tims_data(tims_dict, 0, message, [test_id])

        except AssertionError as ae:
            message = str(ae)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        except Exception as e:
            message = str(e)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        finally:
            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, pps_host, \
                                  householdid, pps_headers, timeout)
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content_reset)
            print message
            return tims_dict


def timeDiff(timestamp):
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

