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
    update_tims_data, cleanup_household, get_household_region,
    fetch_gridRequest, get_contentIddict_bytitle,
    do_PPSbooking, verify_booking, delete_PPSbooking,
    get_vmr_response, fetch_recordingCatalog
)
from RRcommonFunctions import ConfigureSRT
from genChannelLineup import *


TESTCASE_STEPS = """
#########################################################################
# TestcaseId: TC10120
# TestcaseSteps: BRB - Dual VMR - Redirect recording before scheduling to different VMR for 
                 different channels with different copy type in SRT.
# 1. Ingest an event on channel 1, 2, 3, 4 & 5 with n minutes duration and n minues post time.
# 2. Modify the SRT in such a way to record the contents as below,
#     RR1|Ch1|RR2|Common
#     RR1|Ch2|RR2|Unique
#     RR1|Ch3|INVALID RR|Common
#     RR1|Ch4|RR2|Common
#     RR1|Ch5|RR2|Unique
# 3. Perform booking for the ingested contents as below.
#    Perform an booking for the contents from channel 1 from hh1. 
#    Perform an booking for the contents from channel 2 from hh2.
#    Perform an booking for the contents from channel 3 from hh3.
#    Perform an booking for the contents from channel 4 from hh4.
#    Perform an booking for the contents from channel 5 from hh5.
# 4. Wait for the program to start its recording on all four households.
# 5. Confirm that except hh3 all hhs contents are in recording state.Also confirm that hh1, hh2, hh4, 
#     hh5 has its content recording as per the rule specified in SRT.
# 6. Cleanup the households and srt table.
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
    test_id = "TC10120"
    tims_dict = {test_id: ["US78110", message, status]}
    print "%s: BRB - Dual VMR - Redirect recording before scheduling to different VMR " \
          "for different channels with different copy type in SRT." % (test_id)

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
        ch1 = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["channels"][0]
        ch2 = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["channels"][1]
        ch3 = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["channels"][2]
        ch4 = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["channels"][3]
        ch5 = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["channels"][4]
        testchannel1 = cfg['test_channels'][ch1]['ServiceId']
        testchannel2 = cfg['test_channels'][ch2]['ServiceId']
        testchannel3 = cfg['test_channels'][ch3]['ServiceId']
        testchannel4 = cfg['test_channels'][ch4]['ServiceId']
        testchannel5 = cfg['test_channels'][ch5]['ServiceId']

        serviceIdlist.append(unicode(testchannel1))
        serviceIdlist.append(unicode(testchannel2))
        serviceIdlist.append(unicode(testchannel3))
        serviceIdlist.append(unicode(testchannel4))
        serviceIdlist.append(unicode(testchannel5))

        prefix = cfg['basic_feature']['household_prefix']
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        recordingstatecheck_timedelay = cfg['pps']['booked_to_recording_delay']
        recording_to_recorded_delay = cfg['pps']['recording_to_recorded_delay']
        householdid1 = prefix + '0'
        householdid2 = prefix + '1'
        householdid3 = prefix + '2'
        householdid4 = prefix + '3'
        householdid5 = prefix + '4'
        householdid_list = [householdid1, householdid2, householdid3, householdid4, householdid5]
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts, upm_hosts))
        broadcasting_starttime = 0
        broadcasting_endtime = 0
        recording_delay = 60
        common_copy = "COMMON"
        unique_copy = "UNIQUE"
        source_region = cfg["feature"]["brb"]["Recorderegions"]["v2pcVMR"]["name"]
        dest_region = cfg["feature"]["brb"]["Recorderegions"]["standaloneVMR"]["name"]
        invalid_region = "Invalid"
        copy_type = unique_copy
        ingest_delay = 120
        vmr = cfg['feature']['brb']['Recorderregions']['v2pcVMR']['host']
        aws_vmr = cfg['feature']['brb']['Recorderregions']['standaloneVMR']['host']
        print "VMR : ", vmr
        print "AWS_VMR :", aws_vmr

        region_index = 5
        contentURI_list = []

        srt_content = [[source_region, str(testchannel1), dest_region, common_copy],
                       [source_region, str(testchannel2), dest_region, unique_copy],
                       [source_region, str(testchannel3), invalid_region, common_copy],
                       [source_region, str(testchannel4), dest_region, common_copy],
                       [source_region, str(testchannel5), dest_region, unique_copy]]

        srt_content_reset = [[source_region, "*", source_region, "NoChange"]]

        # Do PPS Booking
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        ###########################  USER DEFINED POST TIME IN UTC ############################
        start_delay = 5
        timeslotinminutes = cfg["test_channels"]["mediumProgramLength"] * 2
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
        channel1.add_to_lineup(serviceId=testchannel1, timeSlotLengthMinutes=timeslotinminutes,
                               timeSlotCount=1, programIDPrefix=eventtitle1)
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

        channel3 = ChannelLineup(BoundaryInMinutes=0)
        channel3.add_to_lineup(serviceId=testchannel3, \
                               timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=1, \
                               programIDPrefix=eventtitle1)
        channel3.postXmlData(ci_host, ci_port, startTime=post_time)
        channel3.writeXmlFiles(startTime=post_time)

        print "channel3 : ", channel3

        channel4 = ChannelLineup(BoundaryInMinutes=0)
        channel4.add_to_lineup(serviceId=testchannel4, \
                               timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=1, \
                               programIDPrefix=eventtitle1)
        channel4.postXmlData(ci_host, ci_port, startTime=post_time)
        channel4.writeXmlFiles(startTime=post_time)

        print "channel4 : ", channel4

        channel5 = ChannelLineup(BoundaryInMinutes=0)
        channel5.add_to_lineup(serviceId=testchannel5, \
                               timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=1, \
                               programIDPrefix=eventtitle1)
        channel5.postXmlData(ci_host, ci_port, startTime=post_time)
        channel5.writeXmlFiles(startTime=post_time)

        print "channel5 : ", channel5

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

            print "Ensure four household present in the system pointing to " \
                  "RR1 recording region. ###\n"
            for household in householdid_list:
                hh_region = get_household_region(cfg, upm_host, household, timeout)
                assert hh_region == source_region, "Testcase Fail : Household %s not in the " \
                                                   "source region %s" % (household, source_region)

            print "### STEP2. Modify the SRT in such a way to record the contents as below,"
            print "           RR1|Ch1|RR2|Common"
            print "           RR1|Ch2|RR2|Unique"
            print "           RR1|Ch3|INVALID RR|Common"
            print "           RR1|Ch4|RR2|Common"
            print "           RR1|Ch5|RR2|Unique ###### \n"
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.set_srt_availability(cfg, state="Enable")
            configureSRT_instance.modify_srt(cfg, srt_content)

            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, pps_host, \
                                  householdid, pps_headers, timeout)

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
            content_ev3 = contentId_list[2][0]
            content_ev4 = contentId_list[3][0]
            content_ev5 = contentId_list[4][0]

            household_content_list = []
            for householdid, content_evt in zip(householdid_list, contentId_list):
                content_evt = list(content_evt)
                payload_evt = """{
                                "scheduleInstanceId" : "%s",
                                "checkConflicts" : true,
                                "pvr":"nPVR"
                                }""" % (content_evt[0])
                household_content_list.append([householdid, content_evt[0], payload_evt])

            print "### STEP3. Perform booking for the ingested contents as below."
            print "           Perform an booking for the contents from channel 1 from hh1."
            print "           Perform an booking for the contents from channel 2 from hh2."
            print "           Perform an booking for the contents from channel 3 from hh3."
            print "           Perform an booking for the contents from channel 4 from hh4."
            print "           Perform an booking for the contents from channel 5 from hh5.### \n"
            for householdid, content_ev, payload_ev in household_content_list:
                result = do_PPSbooking(pps_port, protocol, pps_host, householdid, \
                                       pps_headers, payload_ev, content_ev, timeout, printflg)
                assert result == "PASS", "Testcase Failed:Unable to do pps booking of content ID " \
                                         + str(content_ev) + " in household " + str(householdid)

            print "### STEP4: Wait for the program to start its recording on all " \
                  "four households. ##### \n \n"
            time.sleep(fetch_bookingcatalog_delay)
            # Getting Catalog Response for the Booked Catalog
            for (householdid, content_ev, payload_ev) in household_content_list:
                catalogresult, catalogresponse = verify_booking(pps_port, protocol, pps_host, \
                                                                householdid, content_ev, timeout)
                if catalogresult == "PASS":
                    jsonresponse = json.loads(catalogresponse.content)
                    for items in jsonresponse:
                        try:
                            if items['scheduleInstance'] == content_ev:
                                broadcasting_starttime = items['content']['broadcastDateTime']
                                broadcasting_endtime = items['content']['endAvailability']
                        except:
                            pass
                else:
                    message = "TestCase  Failed : Content ID " + str(content_ev) + " in household " \
                              + str(householdid) + " is not in the BOOKED state"
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

            print "### STEP5: Confirm that except hh3 all hhs contents are in recording state." \
                  "Also confirm that hh1, hh2, hh4, hh5 has its content recording as " \
                  "per the rule specified in SRT.##### \n \n"

            for householdid, content_ev, payload_ev in household_content_list:
                recrding_res, recrding_resp = verify_recording_state(pps_port, protocol, pps_host,
                                                                       householdid, content_ev,
                                                                       timeout)
                if recrding_res != "PASS":
                    message = "Testcase Failed: Content ID {0} in household {1} is " \
                              "not in the RECORDING state".format(content_ev, householdid)
                    assert False, message

            cfg['vmr']['host'] = aws_vmr
            copy_type_list = []
            region_list = []
            for householdid, content_ev, payload_ev in household_content_list:
                if householdid == householdid3:
                    continue
                playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, [content_ev], \
                                                       [householdid], timeout)
                assert playbackuri_list is not None, "TestCase failed: Unable to get recording catalog"
                print "Playback URI list :", playbackuri_list
                contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
                print "ContentId list :", contentidlist
                vmr_response = get_vmr_response(cfg, contentidlist[0], timeout)
                recording_hh = json.loads(vmr_response.content)[0]
                copy_type_hh = recording_hh["CopyType"]
                region_hh = recording_hh['A8UpdateURL'].split('/')[region_index]
                copy_type_list.append(copy_type_hh)
                region_list.append(region_hh)

            assert copy_type_list[0] == copy_type_list[3] == common_copy, \
                "Testcase Failed: Contents are not in expected copy " \
                "type %s in household 1 and 4."
            assert copy_type_list[1] == copy_type_list[4] == unique_copy, \
                "Testcase Failed: Contents are not in expected copy " \
                "type %s in household 2 and 5."

            assert region_list[0] == region_list[1] == region_list[3] == region_list[4] == dest_region, \
                "Testcase Failed: Contents are not in expected region " \
                " %s in household 3 and 4." % (dest_region)

            message = "Testcase Passed: SRT is working as expected."

        except AssertionError as ae:
            message = str(ae)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        except Exception as e:
            message = str(e)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        finally:
            print "STEP7. Cleanup the households and srt table."
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
