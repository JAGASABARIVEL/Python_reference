#!/usr/bin/python
import os
import sys
import json
from pprint import pprint
import time
import calendar
import itertools
import datetime
import mypaths
import random
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
from genChannelLineup import *
from RRcommonFunctions import ConfigureSRT

###################################################################################################
# TestcaseId: TC9588
# TestcaseSteps: Big Red Button - static_routing_table.txt rename to invalid name.
# STEP1: Ingest an event of n minutes with the posttime of n Minutes to the CI Host
# STEP2: Fetching the grid response to collect the ingested content.
# STEP3: Do the PPS Booking of the ingested event, verify booking is successful
# STEP4: Rename the SRT file name to some invalid name
# STEP5: Wait till the start of the event and verify the recording state of the event
# STEP6: Verify the content is recorded
###################################################################################################


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
    test_id = "TC9588"
    tims_dict = {
                test_id:["US79248", message, status],
                }
    print "%s: Big Red Button - static_routing_table.txt rename to invalid name."% (test_id)

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

        #Initialize the Variables
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
        recordedstatecheck_timedelay = cfg['pps']['recording_to_recorded_delay']
        householdlimit = cfg['feature']['households_needed']
        index = random.randint(0, householdlimit - 1)
        householdid = prefix + str(index)
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts))
        broadcasting_starttime = 0

        source_region = cfg["recorderRegion"]
        dest_region = "invalid"
        invalid_srt = "routing_table.txt"

        # Do PPS Booking
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }

        ###########################  USER DEFINED POST TIME IN UTC ############################
        start_delay = 3
        timeslotinminutes = cfg["test_channels"]["longProgramLength"] * 2
        ingestion_time = get_utc_time_after_n_minutes(start_delay, True)
        start_time = datetime.datetime.strptime(ingestion_time, '%Y-%m-%dT%H:%M:%S')
        post_time = calendar.timegm(start_time.timetuple()) + 0.0001
        #######################################################################################

        print "### STEP1: Ingest an event of n minutes with the posttime of n Minutes to the CI Host ###\n"
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']

        eventtitle1 = "tc9588" + str(random.randint(1, 499))

        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=testchannel1, timeSlotLengthMinutes=timeslotinminutes,
                              timeSlotCount=2, programIDPrefix=eventtitle1)
        channel.postXmlData(ci_host, ci_port, startTime=post_time)
        channel.writeXmlFiles(startTime=post_time)
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute

        print "Script will wait for %s seconds for catalog ingest." % sleep_channel
        time.sleep(sleep_channel)

    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, [test_id])
        return tims_dict

    for (cmdc_host, pps_host) in hostlist:
        try:
            # Cleanup Household
            cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)

            print "### STEP2: Fetching the grid response to collect the ingested content. ###\n"
            gridservicelistresponse = fetch_gridRequest(catalogueId, protocol, cmdc_host,
                                                        cmdc_port, serviceIdlist, region,
                                                        timeout, printflg)
            assert gridservicelistresponse, "Testcase Failed: Unable to Fetch Grid Response"

            contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse, eventtitle1,
                                                           ['title'])
            print "ContentID dictionary from the Grid Response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable to Form ContentId dictionary " \
                                       "from the Grid Response"

            contentId_list = sorted(contentId_dict_all.items(), key=lambda x: x[1])
            print "ContentId list after Sorting\n" + str(contentId_list)
            assert (len(contentId_list) > 0), "Testcase Failed: Unable to form ContentId " \
                                              "list from ContentId dictionary"

            content_ev1 = contentId_list[0][0]
            broadcasting_starttime = contentId_list[0][1][0]
            broadcast_endtime = contentId_list[0][1][1]

            payload_ev1 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev1)

            print "### STEP3: Do the PPS Booking of the ingested event, verify booking is " \
                  "successful ###\n"

            result = do_PPSbooking(pps_port, protocol, pps_host, householdid, pps_headers,
                                   payload_ev1, content_ev1, timeout, printflg)
            assert result == "PASS", "Testcase Failed: Unable to do pps booking of content ID " + str( content_ev1)

            time.sleep(fetch_bookingcatalog_delay)

            catalogresult, catalogresponse = verify_booking(pps_port, protocol, pps_host,
                                                            householdid, content_ev1, timeout)
            # print "Booking response :", catalogresult

            assert catalogresult == "PASS", "TestCase  Failed : Content ID " + str(content_ev1) + " is not in the BOOKED state"

            print "PPS Booking is successful for the event contentid ", content_ev1

            print "### STEP4: Rename the SRT file name to some invalid name ###\n"
            configureSRT_instance = ConfigureSRT()
            res = configureSRT_instance.change_srt_file(cfg, srt_name=invalid_srt)
            assert res, "Testcase Failed: Unable to rename the SRT file"

            print "### STEP5: Verify the recording state of the event ### \n"

            recordingstatechage = recordingstatecheck_timedelay + get_timedifference(broadcasting_starttime, printflg)
            print "Script will wait for " + str( recordingstatechage ) + " seconds to check " \
                                                                         "the event recording state"
            time.sleep(recordingstatechage)

            recording_res, recording_resp = verify_recording_state(pps_port, protocol, pps_host, householdid, content_ev1, timeout)
            assert recording_res == "PASS", "Testcase Failed: Content ID {0} is not in the RECORDING state".format(content_ev1)
            print "Event is in Recording state"

            print "### STEP6:  Verify the content is recorded ###\n"
            recordedstatechage = recordedstatecheck_timedelay + get_timedifference(broadcast_endtime, printflg)
            print "Script will wait for " + str(recordedstatechage) + " seconds to complete recording"

            ## VMR Verification
            playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol,
                                                       [content_ev1], householdid, timeout)
            assert playbackuri_list, "Testcase Failed : Unable to get the contentplay uri"
            print "Contentplay URI :", playbackuri_list
            contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
            assert contentidlist, "Testcase Failed : Unable to get the contentId"
            print "ContentId list :", contentidlist

            vmr_response_1 = get_vmr_response(cfg, contentidlist[0], timeout)
            assert vmr_response_1, "Testcase Failed : Unable to get the VMR response."
            riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
            print "riodev_recording_hh1 : ", riodev_recording_hh1

            rr = riodev_recording_hh1["A8UpdateURL"].split('/')[-1]
            assert rr == source_region, "Testcase Failed : Recorder region is changed when the SRT file is renamed"

            message = "TestCase Passed : Renamed the SRT and the recording is successful"
            tims_dict = update_tims_data(tims_dict, 0, message, [test_id])

        except AssertionError as ae:
            message = str(ae)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        except Exception as e:
            message = str(e)
            tims_dict = update_tims_data(tims_dict, 1, message, [test_id])

        finally:
            try:
                print "Renaming the SRT file to original value"
                configureSRT_instance.change_srt_file(cfg, srt_name=invalid_srt, revert=True)
            except:
                pass
            # Cleanup HH
            cleanup_household(cfg, pps_port, protocol, pps_host, householdid, pps_headers, timeout)
            print message
            return tims_dict


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
