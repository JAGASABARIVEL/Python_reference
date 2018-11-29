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
    get_vmr_response, playback_recordedevent, verify_recorded_state, get_household_region
)
from RRcommonFunctions import ConfigureSRT
from genChannelLineup import *


'''#########################################################################
TestcaseId: TC10117
Testcase: BRB - Dual VMR - Redirect the request to different VMR for a single channel in Common 
          copy mode and playback the content
1. Ingest an event on channel 1 & channel 2 with n minutes duration and n mintues post time.
2. Ensure four household present in the system pointing to RR1 recording region.
3. Perform booking on all four households for the ingested contents.
   4.1. Perform the booking on channel 1 on hh 1 & 2.
   4.2. Perform the booking on channel 2 on hh 3 & 4.
4. Wait for the program to start its recording on all four households.
5. Modify the SRT in such a way to record the contents from channel 1 with common copy type 
   in Y recording region.
6. Wait for the content to move to recorded state and confirm playback happening on all households.
7. Cleanup the households and srt table.

SRT Config:
RR1|Ch1|RR2|Common
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
    test_id = "TC10117"
    tims_dict = {test_id: ["US78110", message, status]}
    print "%s: BRB - Dual VMR - Redirect the request to different VMR for a single channel in" \
          " Common copy mode and playback the content" % (test_id)

    try:
        # announce
        abspath = os.path.abspath(__file__)
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
        cmdc_port = cfg['cmdc']['port']
        upm_hosts = [cfg['upm']['host']]
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']

        # Playback config
        prmsupportedflag = cfg['prm_supported']
        proxyhostcheckflag = cfg['proxyHostNeeded']
        proxy_host = cfg['proxyhost']['host']
        proxy_port = cfg['proxyhost']['port']
        contentplayback_host = cfg['contentplayback']['host']
        contentplayback_port = cfg['contentplayback']['port']
        contentplayback_url = cfg['contentplayback']['url']
        rm_host = cfg['rm']['host']

        # Hardcoded the channel due to UUID channel issue while routing and recording.
        route_channel = '5b89b327-920f-402c-900d-1fb1e1784310' #UUID equivalet of cfg['test_channels']['GenericCh1']['ServiceId']
        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        testchannel2 = cfg['test_channels']['GenericCh2']['ServiceId']

        serviceIdlist.append(unicode(testchannel1))
        serviceIdlist.append(unicode(testchannel2))

        prefix = cfg['basic_feature']['household_prefix']
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        recordingstatecheck_timedelay = cfg['pps']['booked_to_recording_delay']
        householdid1 = prefix + '1'
        householdid2 = prefix + '2'
        householdid3 = prefix + '3'
        householdid4 = prefix + '4'
        householdid_list = [householdid1, householdid2, householdid3, householdid4]
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts, upm_hosts))
        broadcasting_starttime = 0
        broadcasting_endtime = 0
        recording_delay = 60

        source_region = cfg["recorderRegion"]
        srt_content_reset = [[source_region, testchannel1, source_region, "NoChange"]]
        common_copy = "Common"
        unique_copy = "Unique"
        dest_region = cfg["recorderRegion2"]
        copy_type = unique_copy
        ingest_delay = 120
        vmr = cfg['vmr']
        aws_vmr = cfg['vmr2']
        region_index = 5

        srt_content = [[source_region, testchannel1, dest_region, common_copy]]

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

        print "### STEP1: Ingest an event on channel 1 & channel 2 with 5 minutes duration and " \
              "5 minues post time. ##### \n \n"
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']

        eventtitle1 = "TC10117" + str(random.randint(1, 499))

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

        print "Wait time for the catalog ingest to " \
              "get synced with the CI Host in seconds: " + str(ingest_delay)
        time.sleep(ingest_delay)

    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
        return tims_dict

    for (cmdc_host, pps_host, upm_host) in hostlist:
        try:
            # Cleaning up the household
            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers,
                                  timeout)

            gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host, \
                                                        cmdc_port, serviceIdlist, region, timeout,
                                                        printflg)
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

            print "### STEP2 : Ensure four household present in the system pointing to " \
                  "RR1 recording region. ###\n"
            for household in householdid_list:
                hh_region = get_household_region(cfg, upm_host, household, timeout)
                assert hh_region == source_region, "Testcase Fail : Household %s not in the " \
                                                   "source region %s" % (household, source_region)

            print "### STEP3: Perform booking on all four households for the ingested content.###\n"
            print "### STEP3.1. Perform the booking on channel 1 on hh 1 & 2###\n"
            content_ev1 = contentId_list[0][0]
            broadcasting_starttime = contentId_list[0][1][0]
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

            print "### STEP3.2. Perform the booking on channel 2 on hh 3 & 4###\n"
            content_ev2 = contentId_list[1][0]
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
                                                + " in household " + str(householdid) + \
                                                " is not in the BOOKED state"

            for householdid in householdid_list[2:4]:
                catalogresult, catalogresponse = verify_booking(pps_port, protocol, pps_host,
                                                                householdid, content_ev2, timeout)
                print "Booking response of Event 2 :\n", catalogresult
                assert catalogresult == "PASS", "TestCase  Failed : Content ID " \
                                                + str(content_ev1) + " in household " + \
                                                str(householdid) + " is not in the BOOKED state"

            print "### STEP4. Wait for the program to start its recording on all four " \
                  "households.####\n"
            broadcasting_starttime = get_timedifference(broadcasting_starttime, printflg)
            recordingstatechage = recordingstatecheck_timedelay + broadcasting_starttime
            print "Script will wait for " + str(recordingstatechage / 60) \
                  + " minutes to check the event recording state"
            time.sleep(recordingstatechage)
            print "Waiting additional %s seconds to workaround the " \
                  "state change issue." % (recording_delay)
            time.sleep(recording_delay)
            time.sleep(120)

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
                              "RECORDING state".format(content_ev1, householdid)
                    assert False, message

            print "### STEP5. Modify the SRT in such a way to record the contents from " \
                  "channel 1 with common copy type in Y recording region. ###\n"
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content)

            print "Verifying the recorded region"
            cfg['vmr'] = aws_vmr
            playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol,
                                                       [content_ev1], householdid_list[:2], timeout)
            print "Playback URI list :", playbackuri_list
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            print "ContentId list :", contentidlist
            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
            riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
            riodev_recording_hh2 = json.loads(vmr_response_2.content)[0]
            region_hh1 = riodev_recording_hh1['A8UpdateURL'].split('/')[region_index]
            region_hh2 = riodev_recording_hh2['A8UpdateURL'].split('/')[region_index]
            copy_type_hh1 = riodev_recording_hh1["CopyType"]
            copy_type_hh2 = riodev_recording_hh2["CopyType"]

            print "riodev_recording_hh1 : ", riodev_recording_hh1
            print "riodev_recording_hh2 : ", riodev_recording_hh2

            print "region_hh1 : ", region_hh1
            print "region_hh2 : ", region_hh2
            assert copy_type_hh1 == copy_type_hh2 == common_copy , \
                "Testcase Failed: Content %s are not in expected copy " \
                "type %s in household 1 and 2." % (content_ev1, copy_type)

            assert region_hh1 == region_hh2 == dest_region, \
                "Testcase Failed: Content %s are not in expected region " \
                " %s in household 1 & household 2." % (content_ev1, dest_region)

            cfg['vmr'] = vmr
            playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, [content_ev2],
                                                       householdid_list[2:4], timeout)
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
            riodev_recording_hh3 = json.loads(vmr_response_1.content)[0]
            riodev_recording_hh4 = json.loads(vmr_response_2.content)[0]
            region_hh3 = riodev_recording_hh3['A8UpdateURL'].split('/')[region_index]
            region_hh4 = riodev_recording_hh4['A8UpdateURL'].split('/')[region_index]
            copy_type_hh3 = riodev_recording_hh3["CopyType"]
            copy_type_hh4 = riodev_recording_hh4["CopyType"]

            print "riodev_recording_hh3 : ", riodev_recording_hh3
            print "riodev_recording_hh4 : ", riodev_recording_hh4

            print "region_hh3 : ", region_hh3
            print "region_hh4 : ", region_hh4

            assert copy_type_hh3 == copy_type_hh4 == unique_copy, \
                "Testcase Failed: Content %s are not in expected copy " \
                "type %s in household 3 and 4." % (content_ev2, copy_type)

            assert region_hh3 == region_hh4 == source_region, \
                "Testcase Failed: Content %s are not in expected region " \
                " %s in household 3 and 4." % (content_ev2, dest_region)

            print "### STEP6. Wait for the content to move to recorded state and confirm playback" \
                  " happening on all households. ###\n"
            # Verify Recorded State
            recorded_res, recorded_response = verify_recorded_state(pps_port, protocol, pps_host,
                                                                    householdid, [content_ev1, content_ev2],
                                                                    timeout)
            assert recorded_res == "PASS", "Testcase Failed: " + recorded_response

            print "All the programs are in RECORDED state"

            recordedcatalogcontent = json.loads(recorded_response.content)
            for items in recordedcatalogcontent:
                if items['scheduleInstance'] in [content_ev1, content_ev2]:
                    if items['state'] == "RECORDED":
                        recordedtitle = items['title']
                        contentplayuri = items['contentPlayUri']

            print "### STEP7: Wait for the content to move to recorded state and confirm " \
                  "playback happening on all households. ###\n"
            playback_rslt, playback_msg = playback_recordedevent(cfg, abspath, test, pps_headers,
                                                                 pps_port, pps_host,
                                                                 prmsupportedflag,
                                                                 proxyhostcheckflag, protocol,
                                                                 rm_host, contentplayback_host,
                                                                 contentplayback_port, proxy_host,
                                                                 proxy_port, contentplayback_url,
                                                                 contentplayuri, recordedtitle,
                                                                 householdid, timeout, printflg)
            assert playback_rslt == "PASS", "Testcase Failed" + playback_msg
            print playback_msg

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
                cleanup_household(cfg, pps_port, protocol, pps_host, \
                                  householdid, pps_headers, timeout)
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
