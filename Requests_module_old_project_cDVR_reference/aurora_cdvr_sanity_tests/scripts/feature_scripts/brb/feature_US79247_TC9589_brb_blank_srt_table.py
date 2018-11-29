import os
import sys
import json
from pprint import pprint
import time
import requests
import calendar
import itertools
import datetime
import mypaths
import random
from multiprocessing import Process, Queue
from os.path import isfile
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
from genChannelLineup import *
from RRcommonFunctions import ConfigureSRT

########################################################################################################################
# TestcaseId: TC9589, Big Red Button - static_routing_table.txt is blank.
# TestcaseSteps:
# Step1: Ingest an event of n minutes with the posttime of n Minutes to the CI Host
# Step2: Setting the SRT table in such a way to record the contents with unique copy type.
# Step3: Fetching the grid response to collect the ingested content.
# Step4: PPS event-1 on hh-1, hh-2 and hh-3 booking from channel 1 is being done for all three households.
# Step5: Confirming that all three households has the booked item-1 in recording state.
# Step6: Setting the SRT table in such a way to record the contents with common copy type.
# Step7: Ingest an event of n minutes with the posttime of n Minutes to the CI Host
# Step8: Setting the SRT table to blank.
# Step9: Fetching the grid response to collect the ingested content.
# Step10: PPS event-1 on hh-1, hh-2 and hh-3 booking from channel 1 is being done for all three households.
# Step11: Confirming that all three households has the booked item-2 in recording state.
# Step12: Verify the copy type of the recordings, it should be unique since the SRT is blank.
########################################################################################################################


def doit(cfg, printflg=False):
    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        updatevalue = updatetimsresultsjson(cfg,start_time,end_time,rc,'feature')
        return updatevalue
    except:
        print "Error Occurred in Script \n"
        PrintException()
        return 1


def doit_wrapper(cfg, printflg=False):

    message = ""
    status = 3
    test_id = "TC9589"
    userstory_id = "US79247"
    tims_dict = {
                test_id: [userstory_id, message, status],
                }
    print "%s: Big Red Button, static_routing_table.txt is blank." % test_id

    try:
        # announce
        abspath = os.path.abspath(__file__)
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
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        recordingstatecheck_timedelay = cfg['pps']['booked_to_recording_delay']
        householdid1 = prefix + '1'
        householdid2 = prefix + '2'
        householdid3 = prefix + '3'
        householdid_list = [householdid1, householdid2, householdid3]
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts))
        broadcasting_starttime = 0
        common_copy = "COMMON"
        unique_copy = "UNIQUE"
        recording_delay = 60
        source_region = cfg["recorderRegion"]
        dest_region = cfg["recorderRegion"]
        copy_type = unique_copy
        srt_content1 = [[source_region, "*", dest_region, "unique"], ]
        srt_content2 = [[source_region, "*", dest_region, "common"], ]
        srt_content3 = [[]]
        srt_content_reset = [[source_region, "*", dest_region, "NoChange"], ]

        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        ###########################  USER DEFINED POST TIME IN UTC ############################
        start_delay = 5
        timeslotinminutes = cfg["test_channels"]["longProgramLength"]# * 2
        ingestion_time = get_utc_time_after_n_minutes(start_delay, True)
        start_time = datetime.datetime.strptime(ingestion_time, '%Y-%m-%dT%H:%M:%S')
        post_time = calendar.timegm(start_time.timetuple()) + 0.0001
        #######################################################################################

        print "\n[STEP1]: Ingest an event of n minutes with the posttime of n Minutes to the CI Host"
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']

        eventtitle1 = "uniquecp" + str(random.randint(1, 499))
        channel1 = ChannelLineup(BoundaryInMinutes=0)
        channel1.add_to_lineup(serviceId=testchannel1, timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=1,
                               programIDPrefix=eventtitle1)
        channel1.postXmlData(ci_host, ci_port, startTime=post_time)
        channel1.writeXmlFiles(startTime=post_time)

        print "Wait time for the catalog ingest to get synced with the CI Host in seconds: " + str(200)
        time.sleep(120)
    except:
        message = "Testcase Failed: Error occured in configuration" + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
        return tims_dict

    for (cmdc_host,pps_host) in hostlist:
        try:
            print "\n[STEP2]: Setting the SRT table in such a way to record the contents with unique copy type."
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content1)

            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)

            print "\n[STEP3]: Fetching the grid response to collect the ingested content."
            gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host, cmdc_port, serviceIdlist, region,
                                                        timeout, printflg)
            assert gridservicelistresponse, "Testcase Failed: Unable to Fetch Grid Response"

            contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse, eventtitle1, ['title'])
            print "ContentID dictionary from the Grid Response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"

            contentId_list = sorted(contentId_dict_all.items(), key=lambda x: x[1])
            print "ContentId list after Sorting\n" + str(contentId_list)
            assert (len(contentId_list) > 0), "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
            print "len(contentId_list) : ", len(contentId_list)

            content_ev1 = contentId_list[0][0]

            payload_ev1 = """{
                    "scheduleInstanceId" : "%s",
                    "checkConflicts" : true,
                    "pvr":"nPVR"
                }""" % content_ev1

            print "About to start the event 1 booking\n\n"
            print "\n[STEP4]: PPS event-1 on hh-1, hh-2 and hh-3 booking from channel 1 is being done for all three households."
            for householdid in householdid_list:
                result = do_PPSbooking(pps_port, protocol, pps_host, householdid, pps_headers, payload_ev1, content_ev1,
                                       timeout, printflg)
                if result != "PASS":
                    message = "Testcase Failed:Unable to do pps booking of content ID " + str(
                        content_ev1) + " in household " + str(householdid)
                    print message
                    tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

            print "Confirming that the households has the items in booked state."
            time.sleep(fetch_bookingcatalog_delay)
            # Getting Catalog Response for the Booked Catalog
            for householdid in householdid_list:
                catalogresult, catalogresponse = verify_booking \
                    (pps_port, protocol, pps_host, householdid, content_ev1, timeout)
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
                    message = "TestCase  Failed : Content ID " + str(content_ev1) \
                              + " in household " + str(householdid) + " is not in the BOOKED state"
                    assert False, message

            broadcasting_starttime = timeDiff(broadcasting_starttime)
            recordingstatechage = recordingstatecheck_timedelay + broadcasting_starttime
            print "Script will wait for " + str(recordingstatechage / 60) + " minutes to check the event recording state"
            time.sleep(recordingstatechage)
            print "Waiting additional %s seconds to workaround the state change issue." % (recording_delay)
            time.sleep(recording_delay)

            print "\n[STEP5]: Confirming that all three households has the booked item-1 in recording state."
            for householdid in householdid_list:
                recordingcatalogresult, recordingcatalogresponse = verify_recording_state(pps_port, protocol, pps_host,
                                                                                          householdid, content_ev1, timeout)
                if recordingcatalogresult != "PASS":
                    message = "Testcase Failed: Content ID {0} in household {1} is not in the RECORDING state".format(
                        content_ev1, householdid)
                    assert False, message

            playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, [content_ev1], householdid_list,
                                                       timeout)
            print "Playback URI list :", playbackuri_list

            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            print "ContentId list :", contentidlist

            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
            print "copy_type : ", copy_type
            print "riodev_recording_hh1 : ", riodev_recording_hh1
            assert riodev_recording_hh1["CopyType"] == copy_type, "Testcase Failed: Content %s are not in expected " \
                                                                  "copy type %s in household 1 & household 2." % \
                                                                  (content_ev1, copy_type)

        except AssertionError as ae:
            message = str(ae)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        except Exception as e:
            message = str(e)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

    print "\n[STEP6]: Setting the SRT table in such a way to record the contents with common copy type."
    configureSRT_instance = ConfigureSRT()
    configureSRT_instance.modify_srt(cfg, srt_content2)

    ###########################  USER DEFINED POST TIME IN UTC ############################
    start_delay = 5
    timeslotinminutes = cfg["test_channels"]["longProgramLength"] * 2
    ingestion_time = get_utc_time_after_n_minutes(start_delay, True)
    start_time = datetime.datetime.strptime(ingestion_time, '%Y-%m-%dT%H:%M:%S')
    post_time = calendar.timegm(start_time.timetuple()) + 0.0001
    #######################################################################################


    print "\n[STEP7]: Ingest an event of n minutes with the posttime of n Minutes to the CI Host"
    eventtitle1 = "commoncp" + str(random.randint(1, 499))
    channel1 = ChannelLineup(BoundaryInMinutes=0)
    channel1.add_to_lineup(serviceId=testchannel1, timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=1,
                           programIDPrefix=eventtitle1)
    channel1.postXmlData(ci_host, ci_port, startTime=post_time)
    channel1.writeXmlFiles(startTime=post_time)

    print "Wait time for the catalog ingest to get synced with the CI Host in seconds: " + str(200)
    time.sleep(120)

    print "\n[STEP8]: Setting the SRT table to blank."
    configureSRT_instance = ConfigureSRT()
    configureSRT_instance.modify_srt(cfg, srt_content3)

    for (cmdc_host, pps_host) in hostlist:
        try:
            for householdid in householdid_list:
                cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)

            print "\n[STEP9]: Fetching the grid response to collect the ingested content."
            gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host, cmdc_port, serviceIdlist,
                                                        region,
                                                        timeout, printflg)
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

            payload_ev1 = """{
                                        "scheduleInstanceId" : "%s",
                                        "checkConflicts" : true,
                                        "pvr":"nPVR"
                                        }""" % content_ev1

            print "About to start the event 1 booking\n\n"
            print "\n[STEP10]: PPS event-2 on hh-1, hh-2 and hh-3 booking from channel 1 is being done for all three households."
            for householdid in householdid_list:
                result = do_PPSbooking(pps_port, protocol, pps_host, householdid, pps_headers, payload_ev1,
                                       content_ev1,
                                       timeout, printflg)
                if result != "PASS":
                    message = "Testcase Failed:Unable to do pps booking of content ID " + str(
                        content_ev1) + " in household " + str(householdid)
                    print message
                    tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

            print "Confirming that the households has the items in booked state."
            time.sleep(fetch_bookingcatalog_delay)
            # Getting Catalog Response for the Booked Catalog
            for householdid in householdid_list:
                catalogresult, catalogresponse = verify_booking \
                    (pps_port, protocol, pps_host, householdid, content_ev1, timeout)
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
                    message = "TestCase  Failed : Content ID " + str(content_ev1) \
                              + " in household " + str(householdid) + " is not in the BOOKED state"
                    assert False, message

            broadcasting_starttime = timeDiff(broadcasting_starttime)
            recordingstatechage = recordingstatecheck_timedelay + broadcasting_starttime
            print "Script will wait for " + str(
                recordingstatechage / 60) + " minutes to check the event recording state"
            time.sleep(recordingstatechage)
            print "Waiting additional %s seconds to workaround the state change issue." % (recording_delay)
            time.sleep(recording_delay)

            print "\n[STEP11]: Confirming that all three households has the booked item-2 in recording state."
            for householdid in householdid_list:
                recordingcatalogresult, recordingcatalogresponse = verify_recording_state(pps_port, protocol,
                                                                                          pps_host,
                                                                                          householdid, content_ev1,
                                                                                          timeout)
                if recordingcatalogresult != "PASS":
                    message = "Testcase Failed: Content ID {0} in household {1} is not in the RECORDING state".format(
                        content_ev1, householdid)
                    assert False, message

            playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, [content_ev1],
                                                       householdid_list,
                                                       timeout)
            print "Playback URI list :", playbackuri_list

            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            print "ContentId list :", contentidlist

            print "\n[STEP12]: Verify the copy type of the recordings, it should be unique since the SRT is blank."
            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
            print "copy_type : ", copy_type
            print "riodev_recording_hh1 : ", riodev_recording_hh1
            assert riodev_recording_hh1["CopyType"] == copy_type, "Testcase Failed: Content %s are not in expected " \
                                                                  "copy type %s in household 1 & household 2." % \
                                                                  (content_ev1, copy_type)

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
