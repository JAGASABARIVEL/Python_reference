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
    get_utc_time_after_n_minutes, relative_config_file, get_timedifference
)
from L2commonFunctions import (
    get_content_playbackURI, get_contentid_from_recid,
)
from L3commonFunctions import (
    verify_recording_state, updatetimsresultsjson,
    update_tims_data, cleanup_household,
    fetch_gridRequest, get_contentIddict_bytitle,
    do_PPSbooking, verify_booking,
    get_vmr_response, get_household_region, create_household, setCdvrSubscriptionOffers
)
from RRcommonFunctions import ConfigureSRT
from genChannelLineup import *


'''#########################################################################
TestcaseId: TC10139
Testcase: BRB - Dual VMR - Swap the request from VMR1 to VMR2 and vice versa for a Channel
1. Ingest an event on channel 1  with 5 minutes duration and 5 minutes post time.
2. Ensure two household present in the system pointing to RR1 recording region and two more 
   household present in the system pointing to RR2 recording region.
3. Modify the SRT in such a way,
   3.1. To record the contents of hh 1, hh2(RR1 region) and from channel 1 with common copy 
        type in RR2 recording region.
   3.2. To record the contents of hh 3, hh4(RR2 region) and from channel 1 with common copy 
        type in RR1 recording region.
4. Perform booking on all four households for the ingested contents.
   4.1. Perform the booking on channel 1 on hh 1 & hh2.
   4.2. Perform the booking on channel 1 on hh 3 & hh4.
5. Wait for the program to start its recording on all four households.
6. Confirm from VMR API response that recorded contents.
   6.1. Content from channel 1 booked on hh1 & hh2 with common copy type in RR2 recording region.
   6.2. Content from channel 2 booked on hh3 & hh4 with common copy type in RR1 recording region.
7. Cleanup the households and srt table.

SRT Config:
RR1|ch2|RR2|common
RR2|ch1|RR1|common
#########################################################################'''


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
        return (1)


def doit_wrapper(cfg, printflg=False):
    message = ""
    status = 3
    test_id = "TC10139"
    tims_dict = {test_id: ["US78110", message, status]}
    print "%s: BRB - Dual VMR - Swap the request from VMR1 to VMR2 and vice versa for a " \
          "Channel" % (test_id)

    try:
        # announce
        # abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        if "no_brb" in cfg["test-flags"]:
            message = "Testcase Skipped: Skipping the testcase since no_brb flag is enabled."
            print message
            tims_dict = update_tims_data(tims_dict, 2, message, [test_id])
            return tims_dict

        # Initialize the Variables
        timeout = 2
        serviceIdlist = []

        # set values based on config
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        upm_hosts = [cfg['upm']['host']]
        upm_port = cfg['upm']['port']
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']

        ch1 = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["channels"][0]
        ch2 = cfg["feature"]["brb"]["Recorderegions"]["v2pcVMR"]["channels"][0]

        testchannel1 = cfg['test_channels'][ch1]['ServiceId']
        testchannel1_uuid = cfg['test_channels'][ch1]['UUID']
        testchannel2 = cfg['test_channels'][ch2]['ServiceId']
        testchannel2_uuid = cfg['test_channels'][ch2]['UUID']

        serviceIdlist.append(unicode(testchannel1))
        serviceIdlist.append(unicode(testchannel2))

        prefix = cfg['basic_feature']['household_prefix']
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        recordingstatecheck_timedelay = cfg['pps']['booked_to_recording_delay']
        householdid1 = prefix + '1'
        householdid2 = prefix + '2'
        householdid3 = prefix + '5'
        householdid4 = prefix + '6'
        householdid_list = [householdid1, householdid2, householdid3, householdid4]
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts, upm_hosts))
        recording_delay = 180

        cmdcRegion = cfg['cmdcRegion']
        adZone = cfg['adZone']
        marketingTarget = cfg['marketingTarget']

        source_region = cfg["feature"]["brb"]["Recorderegions"]["v2pcVMR"]["name"]
        dest_region = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["name"]
        srt_content_reset = [[source_region, "*", source_region, "NoChange"]]
        common_copy = "COMMON"
        unique_copy = "UNIQUE"
        vmr = cfg["vmr"]["instances"]["v2pcVMR"]
        aws_vmr = cfg["vmr"]["instances"]["standaloneVMR"]
        print "VMR : ", vmr
        print "AWS_VMR :", aws_vmr
        region_index = 5

        srt_content = [[source_region, str(testchannel1_uuid), dest_region, common_copy],
                       [dest_region, str(testchannel2_uuid), source_region, common_copy]]

        # Do PPS Booking
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        # ##########################  USER DEFINED POST TIME IN UTC ############################
        start_delay = 5
        timeslotinminutes = cfg["test_channels"]["longProgramLength"]
        ingestion_time = get_utc_time_after_n_minutes(start_delay, True)
        start_time = datetime.datetime.strptime(ingestion_time, '%Y-%m-%dT%H:%M:%S')
        post_time = calendar.timegm(start_time.timetuple()) + 0.0001
        #######################################################################################

        print "### STEP1: Ingest an event on channel 1  with 5 minutes duration and 5 minutes " \
              "post time. ###\n"
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']

        eventtitle1 = "TC10139" + str(random.randint(1, 499))
        channel1 = ChannelLineup(BoundaryInMinutes=0)
        channel1.add_to_lineup(serviceId=testchannel1, timeSlotLengthMinutes=timeslotinminutes,
                               timeSlotCount=1, programIDPrefix=eventtitle1)
        channel1.postXmlData(ci_host, ci_port, startTime=post_time)
        channel1.writeXmlFiles(startTime=post_time)

        print "channel1 : ", channel1

        channel2 = ChannelLineup(BoundaryInMinutes=0)
        channel2.add_to_lineup(serviceId=testchannel2, timeSlotLengthMinutes=timeslotinminutes,
                               timeSlotCount=1, programIDPrefix=eventtitle1)
        channel2.postXmlData(ci_host, ci_port, startTime=post_time)
        channel2.writeXmlFiles(startTime=post_time)

        print "channel2 : ", channel2

        length = channel1.getTotalLength() + channel2.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute

        print "Wait time for the catalog ingest to " \
              "get synced with the CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)

    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
        return tims_dict

    for (cmdc_host, pps_host, upm_host) in hostlist:
        try:
            # Create HH in AWS_VMR recorder region
            print "### STEP2: Create HH with empty recorder region and Do set offers ###"

            for householdid in householdid_list[2:4]:
                hh_headers = {
                    'Content-Type': 'application/json',
                    'Source-Type': 'WEB',
                    'Source-ID': '127.0.0.1',
                    'Accept': 'application/json'
                }
                hh_create_payload = """
                                        {
                                          "householdId" : "%s",
                                          "householdStatus" : "ACTIVATED",
                                          "operateStatus": "ACTIVE",
                                          "locale" : {
                                                "region" : "%s",
                                                "cmdcRegion":"%s",
                                                "adZone": "%s",
                                                    "marketingTarget": "%s",
                                                    "recorderRegion": "%s"
                                                     },
                                          "cDvrPvr": true
                                    }
                                    """ % (householdid, region, cmdcRegion, adZone,
                                           marketingTarget, dest_region)

                print "Create HouseHold Payload :", hh_create_payload

                create_hh = create_household(protocol, upm_port, householdid, upm_host, hh_headers,
                                         hh_create_payload)
                assert create_hh, "Testcase Failed: Unable to create household %s " \
                                  "in RR %s" %(householdid, dest_region)

                setoffers = setCdvrSubscriptionOffers(cfg, householdid)
                assert setoffers, "Testcase Failed : Unable to set offers for %s" % householdid

            print "### STEP2 : Ensure two household present in the system pointing to RR1 " \
                  "recording region and two more household present in the system pointing to RR2 " \
                  "recording region. ###\n"
            for household in householdid_list[:2]:
                hh_region = get_household_region(cfg, upm_host, household, timeout)
                assert hh_region == source_region, "Testcase Fail : Household %s not in the " \
                                                   "source region %s" % (household, source_region)

            for household in householdid_list[2:4]:
                hh_region = get_household_region(cfg, upm_host, household, timeout)
                assert hh_region == dest_region, "Testcase Fail : Household %s not in the " \
                                                   "dest region %s" % (household, dest_region)

            print "### STEP3:  Modify the SRT in such a way, ###\n"
            print "### STEP 3.1. To record the contents of hh 1, hh2(RR1 region) and from " \
                  "channel 1 with common copy type in RR2 recording region. ###\n"
            print "### STEP 3.2. To record the contents of hh 3, hh4(RR2 region) and from " \
                  "channel 1 with common copy type in RR1 recording region.###\n"

            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content)

            # Cleaning up the household
            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)

            gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host,
                                                        cmdc_port, [unicode(testchannel1), ],
                                                        region, timeout, printflg)
            assert gridservicelistresponse, "Testcase Failed: Unable to Fetch Grid Response"

            contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse, eventtitle1,
                                                           ['title'])
            print "ContentID dictionary from the Grid Response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable " \
                                       "to Form ContentId dictionary from the Grid Response"

            contentId_list = sorted(contentId_dict_all.items(), key=lambda x: x[1])
            print "ContentId list after Sorting\n" + str(contentId_list)
            assert (len(contentId_list) > 0), "Testcase Failed: Unable " \
                                              "to form ContentId list from ContentId dictionary"
            print "len(contentId_list) : ", len(contentId_list)

            content_ev1 = contentId_list[0][0]
            ev1_broadcast_start_time = contentId_list[0][1][0]

            gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host,
                                                        cmdc_port, [unicode(testchannel2), ],
                                                        region, timeout, printflg)
            assert gridservicelistresponse, "Testcase Failed: Unable to Fetch Grid Response"

            contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse, eventtitle1,
                                                           ['title'])
            print "ContentID dictionary from the Grid Response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable " \
                                       "to Form ContentId dictionary from the Grid Response"

            contentId_list = sorted(contentId_dict_all.items(), key=lambda x: x[1])
            print "ContentId list after Sorting\n" + str(contentId_list)
            assert (len(contentId_list) > 0), "Testcase Failed: Unable " \
                                              "to form ContentId list from ContentId dictionary"
            print "len(contentId_list) : ", len(contentId_list)

            content_ev2 = contentId_list[0][0]

            print "### STEP4. Perform booking on all four households for the ingested content.###\n"
            print "## STEP 4.1. Perform the booking on channel 1 on hh 1 & hh2.##"
            payload_ev1 = """{
                                        "scheduleInstanceId" : "%s",
                                        "checkConflicts" : true,
                                        "pvr":"nPVR"
                                        }""" % (content_ev1)

            for householdid in householdid_list[:2]:
                result = do_PPSbooking(pps_port, protocol, pps_host, householdid, \
                                       pps_headers, payload_ev1, content_ev1, timeout, printflg)
                if result != "PASS":
                    message = "Testcase Failed:Unable to do pps booking of content ID " \
                              + str(content_ev1) + " in household " + str(householdid)
                    print message
                    tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

            print "## STEP 4.2. Perform the booking on channel 1 on hh 3 & hh4.##"
            payload_ev2 = """{
                                "scheduleInstanceId" : "%s",
                                "checkConflicts" : true,
                                "pvr":"nPVR"
                                }""" % (content_ev2)

            for householdid in householdid_list[2:4]:
                result = do_PPSbooking(pps_port, protocol, pps_host, householdid, \
                                       pps_headers, payload_ev2, content_ev2, timeout, printflg)
                if result != "PASS":
                    message = "Testcase Failed:Unable to do pps booking of content ID " \
                              + str(content_ev1) + " in household " + str(householdid)
                    print message
                    tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

            time.sleep(fetch_bookingcatalog_delay)
            print "About to start the event 1 booking\n"
            # Getting Catalog Response for the Booked Catalog
            for householdid in householdid_list[:2]:
                catalogresult, catalogresponse = verify_booking(pps_port, protocol, pps_host,
                                                                householdid, content_ev1, timeout)
                print "Booking response of Event 1:", catalogresult
                assert catalogresult == "PASS", "TestCase  Failed : Content ID " + str(content_ev1) \
                                                + " in household " + str(householdid) \
                                                + " is not in the BOOKED state"

            for householdid in householdid_list[2:4]:
                catalogresult, catalogresponse = verify_booking(pps_port, protocol, pps_host,
                                                                householdid, content_ev2, timeout)
                print "Booking response of Event 2 :\n", catalogresult
                assert catalogresult == "PASS", "TestCase  Failed : Content ID " \
                                                + str(content_ev2) + " in household " \
                                                + str(householdid) + " is not in the BOOKED state"

            print "### STEP5.Wait for the program to start its recording on all four " \
                  "households.####\n"

            broadcasting_starttime = get_timedifference(ev1_broadcast_start_time, printflg)
            recordingstatechage = recordingstatecheck_timedelay + broadcasting_starttime
            print "Script will wait for ", recordingstatechage," seconds to check the event " \
                                                               "recording state"
            time.sleep(recordingstatechage)
            print "Waiting additional %s seconds to workaround the " \
                  "state change issue." % (recording_delay)
            time.sleep(recording_delay)

            for householdid in householdid_list[:2]:
                recrding_res1, recrding_resp1 = verify_recording_state(pps_port, protocol, pps_host,
                                                                       householdid, content_ev1,
                                                                       timeout)
                if recrding_res1 != "PASS":
                    message = "Testcase Failed: Content ID {0} in household {1} is " \
                              "not in the RECORDING state".format(content_ev1, householdid)
                    assert False, message

            for householdid in householdid_list[2:4]:
                recrding_res2, recrding_resp2 = verify_recording_state(pps_port, protocol, pps_host,
                                                                       householdid, content_ev2,
                                                                       timeout)
                if recrding_res2 != "PASS":
                    message = "Testcase Failed: Content ID {0} in household {1} is not in the " \
                              "RECORDING state".format(content_ev2, householdid)
                    assert False, message

            print "### STEP 6. Confirm from VMR API response that recorded contents. ###\n"

            print "## STEP6.1. Content from channel 1 booked on hh1 & hh2 with common copy " \
                  "type in RR2 recording region.##"
            cfg['vmr']['host'] = aws_vmr
            playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol,
                                                       [content_ev1], householdid_list[:2], timeout)
            print "Playback URI list :", playbackuri_list
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            print "ContentId list :", contentidlist
            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
            assert vmr_response_1 and vmr_response_1.content != 'null', \
                "Testcase Failed : Unable to get the VMR response for contentId " \
                "%s" % contentidlist[0]
            assert vmr_response_2 and vmr_response_2.content != 'null', \
                "Testcase Failed : Unable to get the VMR response for contentId " \
                "%s" % contentidlist[1]
            riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
            riodev_recording_hh2 = json.loads(vmr_response_2.content)[0]
            region_hh1 = riodev_recording_hh1['A8UpdateURL'].split('/')[region_index]
            region_hh2 = riodev_recording_hh2['A8UpdateURL'].split('/')[region_index]
            hh1_copy_type = riodev_recording_hh1["CopyType"]
            hh2_copy_type = riodev_recording_hh2["CopyType"]

            print "riodev_recording_hh1 : ", riodev_recording_hh1
            print "riodev_recording_hh2 : ", riodev_recording_hh2

            print "region_hh1 : ", region_hh1
            print "region_hh2 : ", region_hh2

            assert hh1_copy_type == hh2_copy_type == common_copy, \
                "Testcase Failed: Content %s are not in expected copy " \
                "type %s in household 1 & household 2." % (content_ev1, common_copy)

            assert region_hh1 == region_hh2 == dest_region, \
                "Testcase Failed: Content %s are not in expected region " \
                " %s in household 1 & household 2." % (content_ev1, dest_region)

            print "## STEP6.2. Content from channel 2 booked on hh3 & hh4 with common copy " \
                  "type in RR1 recording region. ##"

            cfg['vmr']['host'] = vmr
            playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, [content_ev2],
                                                       householdid_list[2:4], timeout)
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            vmr_response_3 = get_vmr_response(cfg, contentidlist[0], timeout)
            vmr_response_4 = get_vmr_response(cfg, contentidlist[1], timeout)
            assert vmr_response_3 and vmr_response_3.content != 'null', \
                "Testcase Failed : Unable to get the VMR response for contentId " \
                "%s" % contentidlist[0]
            assert vmr_response_4 and vmr_response_4.content != 'null', \
                "Testcase Failed : Unable to get the VMR response for contentId " \
                "%s" % contentidlist[1]
            riodev_recording_hh3 = json.loads(vmr_response_3.content)[0]
            riodev_recording_hh4 = json.loads(vmr_response_4.content)[0]
            region_hh3 = riodev_recording_hh3['A8UpdateURL'].split('/')[region_index]
            region_hh4 = riodev_recording_hh4['A8UpdateURL'].split('/')[region_index]
            hh3_copy_type = riodev_recording_hh3["CopyType"]
            hh4_copy_type = riodev_recording_hh4["CopyType"]

            print "riodev_recording_hh3 : ", riodev_recording_hh3
            print "riodev_recording_hh4 : ", riodev_recording_hh4

            print "region_hh3 : ", region_hh3
            print "region_hh4 : ", region_hh4

            assert hh3_copy_type == hh4_copy_type == common_copy, \
                "Testcase Failed: Content %s are not in expected copy " \
                "type %s in household 3." % (content_ev1, common_copy)

            assert region_hh3 == source_region and region_hh4 == source_region, \
                "Testcase Failed: Content %s are not in expected region " \
                " %s in household 3." % (content_ev1, source_region)

            message = "TestCase Passed : SRT is working as expected."
            tims_dict = update_tims_data(tims_dict, 0, message, [test_id])

        except AssertionError as ae:
            message = str(ae)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        except Exception as e:
            message = str(e)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        finally:
            print "### STEP7. Cleanup the households and srt table. ###\n"
            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, pps_host, householdid,
                                  pps_headers, timeout)
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content_reset)
            print message
            return tims_dict


if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    # read config file
    sa = sys.argv
    cfg = relative_config_file(sa, scriptName)
    if cfg['basic_feature']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
        print
    L = doit(cfg, True)
    exit(L)
