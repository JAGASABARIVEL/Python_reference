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
    do_PPSbooking, verify_booking, delete_PPSrecording,
    get_vmr_response, fetch_recordingCatalog,
    verify_recorded_state, get_household_region
)
from RRcommonFunctions import ConfigureSRT
from genChannelLineup import *


TESTCASE_STEPS = """
#########################################################################
# TestcaseId: TC10118
# TestcaseSteps: BRB - Dual VMR - Redirect recording before scheduling to different VMR for a 
#                single channel in Common copy mode and delete the recording once done.
# 1. Ingest an event on channel 1 & channel 2 with 5 minutes duration and 25 minues post time.
# 2. Ensure four household present in the system pointing to RR1 recording region.
# 3. Modify the SRT in such a way to record the contents from channel 1 with common copy type in RR2 recording region.
# 4. Perform booking on all four households for the ingested contents.
#    4.1. Perform the booking on channel 1 on hh 1 & hh2.
#    4.2. Perform the booking on channel 2 on hh 3 & hh4.
# 5. Wait for the program to start its recording on all four households.
# 6. Confirm from VMR API response that recorded contents.
#    6.1. Content from channel 1 recorded on hh1 & hh2 with common copy type in RR2 recording region.
#    6.2. Content from channel 2 recorded on hh3 & hh4 with default copy type in RR1 recording region.
# 7. Delete the recording content and confirm content is removed successfully from the recording catalog.
# 8. Cleanup the households and srt table.

# SRT Config
# RR1 | CH1 | RR2 | Common
#########################################################################
"""
print TESTCASE_STEPS


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
    test_id = "TC10118"
    tims_dict = {test_id: ["US78110", message, status]}
    print "%s: BRB - Dual VMR - Redirect the request to different VMR for a single channel in " \
          "Common copy mode and playback the content." % (test_id)

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
        upm_hosts = [cfg['upm']['host']]
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']

        # Handle if the there are less channels than the threshold.
        threshold_channels = 17
        channelfilter1 = []
        for channels in cfg['test_channels'].keys():
            if channels.startswith("GenericCh"):
                channelfilter1.append(channels)
        if len(channelfilter1) < threshold_channels:
            message = "Skipping this TC since number of channels are less than 17."
            print message
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
            return tims_dict

        # Hardcoded the channel due to UUID channel issue while routing and recording.
        ch1 = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["channels"][1]
        ch2 = cfg["feature"]["brb"]["Recorderegions"]["v2pcVMR"]["channels"][0]
        testchannel1 = cfg['test_channels'][ch1]['ServiceId']
        testchannel2 = cfg['test_channels'][ch2]['ServiceId']

        serviceIdlist.append(unicode(testchannel1))
        serviceIdlist.append(unicode(testchannel2))

        prefix = cfg['basic_feature']['household_prefix']
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        recordingstatecheck_timedelay = cfg['pps']['booked_to_recording_delay']
        recording_to_recorded_delay = cfg['pps']['recording_to_recorded_delay']
        householdid1 = prefix + '1'
        householdid2 = prefix + '2'
        householdid3 = prefix + '3'
        householdid4 = prefix + '4'
        householdid_list = [householdid1, householdid2, householdid3, householdid4]
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts, upm_hosts))
        broadcasting_starttime = 0
        broadcasting_endtime = 0
        recording_delay = 60
        common_copy = "COMMON"
        unique_copy = "UNIQUE"
        source_region = cfg["feature"]["brb"]["Recorderegions"]["v2pcVMR"]["name"]
        dest_region = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["name"]
        copy_type = unique_copy
        ingest_delay = 120
        vmr = cfg['feature']['brb']['Recorderregions']['v2pcVMR']['host']
        aws_vmr = cfg['feature']['brb']['Recorderregions']['standaloneVMR']['host']
        print "VMR : ", vmr
        print "AWS_VMR :", aws_vmr

        region_index = 5
        contentURI_list = []

        srt_content = [[source_region, str(testchannel1), dest_region, common_copy]]
        srt_content_reset = [[source_region, "*", source_region, "NoChange"]]

        # Do PPS Booking
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        ###########################  USER DEFINED POST TIME IN UTC ############################
        start_delay = 5
        timeslotinminutes = cfg["test_channels"]["longProgramLength"] * 2
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

        eventtitle1 = test_id + str(random.randint(1, 499))

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

    for (cmdc_host, pps_host, upm_host) in hostlist:
        try:

            print "### STEP2 : Ensure four household present in the system pointing to " \
                  "RR1 recording region. ###\n"
            for household in householdid_list:
                hh_region = get_household_region(cfg, upm_host, household, timeout)
                assert hh_region == source_region, "Testcase Fail : Household %s not in the " \
                                                   "source region %s" % (household, source_region)

            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, pps_host, \
                                  householdid, pps_headers, timeout)

            print "### STEP3: Modify the SRT in such a way to record the contents from channel 1 " \
                  "with common copy type in RR2 recording region. ###### \n"
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.set_srt_availability(cfg, state="Enable")
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content)


            gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host, cmdc_port, \
                                                        serviceIdlist, region, timeout, printflg)
            assert gridservicelistresponse, "Testcase Failed: Unable to Fetch Grid Response"

            contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse, \
                                                           eventtitle1, ['title'])
            print "ContentID dictionary from the Grid Response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable to Form ContentId " \
                                       "dictionary from the Grid Response"

            contentId_list = sorted(contentId_dict_all.items(), key=lambda x: x[1])
            print "ContentId list after Sorting\n" + str(contentId_list)
            assert (len(contentId_list) > 0), "Testcase Failed: Unable to form ContentId " \
                                              "list from ContentId dictionary"

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

            print "### STEP4. Perform booking on all four households for the ingested contents."
            print "        4.1. Perform the booking on channel 1 on hh 1 & hh2."
            print "        4.2. Perform the booking on channel 2 on hh 3 & hh4. ####### \n"
            for householdid in householdid_list[:2]:
                result = do_PPSbooking(pps_port, protocol, pps_host, householdid, \
                                       pps_headers, payload_ev1, content_ev1, timeout, printflg)
                assert result == "PASS", "Testcase Failed:Unable to do pps booking of content ID " \
                                         + str(content_ev1) + " in household " + str(householdid)

            for householdid in householdid_list[2:4]:
                result = do_PPSbooking(pps_port, protocol, pps_host, householdid, \
                                       pps_headers, payload_ev2, content_ev2, timeout, printflg)
                assert result == "PASS", "Testcase Failed:Unable to do pps booking of content ID " \
                                         + str(content_ev2) + " in household " + str(householdid)

            print "### STEP5: Wait for the program to start its recording on all " \
                  "four households. ##### \n \n"
            time.sleep(fetch_bookingcatalog_delay)
            # Getting Catalog Response for the Booked Catalog
            for householdid in householdid_list[:2]:
                catalogresult, catalogresponse = verify_booking(pps_port, protocol, pps_host, \
                                                                householdid, content_ev1, timeout)
                if catalogresult == "PASS":
                    jsonresponse = json.loads(catalogresponse.content)
                    for items in jsonresponse:
                        try:
                            contentURI = items['uri']
                            contentURI_list.append(contentURI)
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
                catalogresult, catalogresponse = verify_booking(pps_port, protocol, pps_host, \
                                                                householdid, content_ev2, timeout)
                if catalogresult == "PASS":
                    jsonresponse = json.loads(catalogresponse.content)
                    for items in jsonresponse:
                        try:
                            contentURI = items['uri']
                            contentURI_list.append(contentURI)
                            if items['scheduleInstance'] == content_ev2:
                                broadcasting_starttime = items['content']['broadcastDateTime']
                                broadcasting_endtime = items['content']['endAvailability']
                        except:
                            pass
                else:
                    message = "TestCase  Failed : Content ID " \
                              + str(content_ev1) + " in household " + str(householdid) \
                              + " is not in the BOOKED state"
                    assert False, message

            broadcasting_starttime = timeDiff(broadcasting_starttime)
            print "broadcasting_starttime :", broadcasting_starttime
            recordingstatechage = recordingstatecheck_timedelay + broadcasting_starttime
            print "Script will wait for " + str(recordingstatechage / 60) \
                  + " minutes to check the event recording state"
            time.sleep(recordingstatechage)
            print "Waiting additional %s seconds to workaround the " \
                  "state change issue." % (recording_delay)
            time.sleep(recording_delay)

            print "Verifying Recording state"
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

            print "### STEP6: Confirm from VMR API response that recorded contents."
            print "        6.1. Content from channel 1 recorded on hh1 & hh2 with " \
                  "common copy type in RR2 recording region."

            cfg['vmr']['host'] = aws_vmr
            playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, [content_ev1], \
                                                       householdid_list[:2], timeout)
            assert playbackuri_list is not None, "TestCase failed: Unable to get recording catalog"
            print "Playback URI list :", playbackuri_list
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            print "ContentId list :", contentidlist
            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            assert vmr_response_1.content != 'null', "TestCase failed: VMR response for ContentId: %s " \
                                                     "is Null." % contentidlist[0]
            vmr_response_2 = get_vmr_response(cfg, contentidlist[1], timeout)
            assert vmr_response_2.content != 'null', "TestCase failed: VMR response for ContentId: %s " \
                                            "is Null." % contentidlist[1]

            recording_hh1 = json.loads(vmr_response_1.content)[0]
            recording_hh2 = json.loads(vmr_response_2.content)[0]

            region_hh1 = recording_hh1['A8UpdateURL'].split('/')[region_index]
            region_hh2 = recording_hh2['A8UpdateURL'].split('/')[region_index]

            copy_type_hh1 = recording_hh1["CopyType"]
            copy_type_hh2 = recording_hh2["CopyType"]

            print "recording_hh1 : ", recording_hh1
            print "recording_hh2 : ", recording_hh2

            print "region_hh1 : ", region_hh1
            print "region_hh2 : ", region_hh2
            assert copy_type_hh1 == copy_type_hh2 == common_copy , \
                "Testcase Failed: Content %s are not in expected copy " \
                "type %s in household 1 and 2." % (content_ev1, copy_type)

            assert region_hh1 == region_hh2 == dest_region, \
                "Testcase Failed: Content %s are not in expected region " \
                " %s in household 1 & household 2." % (content_ev1, dest_region)

            print "        6.2. Content from channel 2 recorded on hh3 & hh4 with " \
                  "default copy type in RR1 recording region.##### \n \n"

            cfg['vmr']['host'] = vmr
            playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, [content_ev2], \
                                                       householdid_list[2:4], timeout)
            assert playbackuri_list is not None, "TestCase failed: Unable to get recording catalog"
            print "Playback URI list :", playbackuri_list
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            print "ContentId list :", contentidlist
            vmr_response_3 = get_vmr_response(cfg, contentidlist[0], timeout)
            assert vmr_response_3.content != 'null', "TestCase failed: VMR response for ContentId: %s " \
                                            "is Null." % contentidlist[0]

            vmr_response_4 = get_vmr_response(cfg, contentidlist[1], timeout)
            assert vmr_response_4.content != 'null', "TestCase failed: VMR response for ContentId: %s " \
                                            "is Null." % contentidlist[1]

            recording_hh3 = json.loads(vmr_response_3.content)[0]
            recording_hh4 = json.loads(vmr_response_4.content)[0]

            region_hh3 = recording_hh3['A8UpdateURL'].split('/')[region_index]
            region_hh4 = recording_hh4['A8UpdateURL'].split('/')[region_index]

            copy_type_hh3 = recording_hh3["CopyType"]
            copy_type_hh4 = recording_hh4["CopyType"]
            print "recording_hh3 : ", recording_hh3
            print "recording_hh4 : ", recording_hh4

            print "region_hh3 : ", region_hh3
            print "region_hh4 : ", region_hh4

            assert copy_type_hh3 == copy_type_hh4 == unique_copy, \
                "Testcase Failed: Content %s are not in expected copy " \
                "type %s in household 3 and 4." % (content_ev2, copy_type)

            assert region_hh3 == region_hh4 == source_region, \
                "Testcase Failed: Content %s are not in expected region " \
                " %s in household 3 and 4." % (content_ev2, source_region)

            del_count = 0
            for contentURI in contentURI_list:
                delete_result = delete_PPSrecording(pps_port, protocol, pps_host, pps_headers, \
                                                    timeout, contentURI, printflg)
                if delete_result == "PASS":
                    del_count += 1

            assert del_count == 4, "TestCase Failed: Unable to delete all recordings"
            print "Checking again in the Recording catalog"
            for householdid in householdid_list[:2]:
                recrding_res1, recrding_resp1 = verify_recording_state(pps_port, protocol, pps_host,
                                                                       householdid, content_ev1,
                                                                       timeout)
                if recrding_res1 == "PASS":
                    message = "Testcase Failed: Content ID {0} in household {1} is " \
                              " in the RECORDING state".format(content_ev1, householdid)
                    assert False, message

            for householdid in householdid_list[2:4]:
                recrding_res2, recrding_resp2 = verify_recording_state(pps_port, protocol, pps_host,
                                                                       householdid, content_ev2,
                                                                       timeout)
                if recrding_res2 == "PASS":
                    message = "Testcase Failed: Content ID {0} in household {1} is in " \
                              "RECORDING state".format(content_ev1, householdid)
                    assert False, message


            message = "Testcase Passed: SRT is working as expected."

        except AssertionError as ae:
            message = str(ae)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        except Exception as e:
            message = str(e)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        finally:
            print "### STEP7. Cleanup the households and srt table. ##### \n \n"
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
    if cfg['basic_feature']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
        print
    L = doit(cfg, True)
    exit(L)
