#!/usr/bin/python
import os
import json
import sys
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
# TestcaseId: TC9641
# TestcaseSteps: Big Red Button, static_routing_table.txt contains 50 items.
# STEP1: Ingest an events of n minutes with the posttime of n Minutes to the CI Host on 50 channels.
# STEP2: Set the SRT table in such a way to record the contents with specific copy type from the concerned channels.
# STEP3: Fetch the grid response to collect the ingested content.
# STEP4: Perform PPS event booking from all four households.
# STEP5: Confirm that all four households has its booked items in booked state.
# STEP6: Confirm that all four households has its booked items in recording state.
# STEP7: Confirm that all households, recording its contents with specific copy type as set in static_route_table.
##########################################################################


def doit(cfg, printflg=False):
    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        updatevalue = updatetimsresultsjson(
            cfg, start_time, end_time, rc, 'feature')
        return updatevalue
    except BaseException:
        print "Error Occurred in Script \n"
        PrintException()
        return (1)


def doit_wrapper(cfg, printflg=False):

    message = ""
    status = 3
    test_id = "TC9641"
    test_id2 = "TC9585"
    test_id3 = "TC9668"
    test_id4 = "TC9840"
    tims_dict = {
        test_id: ["US79412", message, status],
        test_id2: ["US79252", message, status],
        test_id3: ["US80008", message, status],
        test_id4: ["US80598", message, status],
    }
    print "%s: Big Red Button, static_routing_table.txt contains 50 items." % (test_id)
    print "%s: Big Red Button - static_routing_table.txt file "\
        "edited - change copyType to NoChange." % (test_id2)
    print "%s Big Red Button - static_routing_table.txt file edited - "\
        "change only copyType" % (test_id3)
    print "%s: Big Red Button - SRT with UC, CC and NoChange for 3 channels." % (test_id4)

    try:
        # announce
        #abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        if "no_brb" in cfg["test-flags"]:
            message = "Testcase Skipped: Skipping the testcases since no_brb flag is enabled."
            print message
            tims_dict = update_tims_data(tims_dict, 2, message, [test_id, test_id2, test_id3, test_id4])
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

        # Handle if the there are less channels than the threshold.
        threshold_channels = 15
        channelfilter1 = []
        for channels in cfg['test_channels'].keys():
            if channels.startswith("GenericCh"):
                channelfilter1.append(channels)
        if len(channelfilter1) < threshold_channels:
            message = "Skipping this TC since number of channels are less than 17."
            print message
            tims_dict = update_tims_data(
                tims_dict, 1, message, [
                    test_id, test_id2,
                    test_id3, test_id4])
            return tims_dict

        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        testchannel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        testchannel3 = cfg['test_channels']['GenericCh3']['ServiceId']
        testchannel4 = cfg['test_channels']['GenericCh4']['ServiceId']
        testchannel5 = cfg['test_channels']['GenericCh5']['ServiceId']
        testchannel6 = cfg['test_channels']['GenericCh6']['ServiceId']
        testchannel7 = cfg['test_channels']['GenericCh7']['ServiceId']
        testchannel8 = cfg['test_channels']['GenericCh8']['ServiceId']
        testchannel9 = cfg['test_channels']['GenericCh9']['ServiceId']
        testchannel10 = cfg['test_channels']['GenericCh10']['ServiceId']
        testchannel11 = cfg['test_channels']['GenericCh11']['ServiceId']
        testchannel12 = cfg['test_channels']['GenericCh12']['ServiceId']
        testchannel13 = cfg['test_channels']['GenericCh13']['ServiceId']
        testchannel14 = cfg['test_channels']['GenericCh14']['ServiceId']
        testchannel15 = cfg['test_channels']['GenericCh15']['ServiceId']
        testchannel16 = cfg['test_channels']['GenericCh16']['ServiceId']
        testchannel17 = cfg['test_channels']['GenericCh17']['ServiceId']
        testchannel18 = 18
        testchannel19 = 19
        testchannel20 = 20
        testchannel21 = 21
        testchannel22 = 22
        testchannel23 = 23
        testchannel24 = 24
        testchannel25 = 25
        testchannel26 = 26
        testchannel27 = 27
        testchannel28 = 28
        testchannel29 = 29
        testchannel30 = 30
        testchannel31 = 31
        testchannel32 = 32
        testchannel33 = 33
        testchannel34 = 34
        testchannel35 = 35
        testchannel36 = 36
        testchannel37 = 37
        testchannel38 = 38
        testchannel39 = 39
        testchannel40 = 40
        testchannel41 = 41
        testchannel42 = 42
        testchannel43 = 43
        testchannel44 = 44
        testchannel45 = 45
        testchannel46 = 46
        testchannel47 = 47
        testchannel48 = 48
        testchannel49 = 49
        testchannel50 = 50

        serviceIdlist.append(unicode(testchannel1))
        serviceIdlist.append(unicode(testchannel2))
        serviceIdlist.append(unicode(testchannel3))
        serviceIdlist.append(unicode(testchannel4))
        serviceIdlist.append(unicode(testchannel5))
        serviceIdlist.append(unicode(testchannel6))
        serviceIdlist.append(unicode(testchannel7))
        serviceIdlist.append(unicode(testchannel8))
        serviceIdlist.append(unicode(testchannel9))
        serviceIdlist.append(unicode(testchannel10))
        serviceIdlist.append(unicode(testchannel11))
        serviceIdlist.append(unicode(testchannel12))
        serviceIdlist.append(unicode(testchannel13))
        serviceIdlist.append(unicode(testchannel14))
        serviceIdlist.append(unicode(testchannel15))
        serviceIdlist.append(unicode(testchannel16))
        serviceIdlist.append(unicode(testchannel17))
        serviceIdlist.append(unicode(testchannel18))
        serviceIdlist.append(unicode(testchannel19))
        serviceIdlist.append(unicode(testchannel20))
        serviceIdlist.append(unicode(testchannel21))
        serviceIdlist.append(unicode(testchannel22))
        serviceIdlist.append(unicode(testchannel23))
        serviceIdlist.append(unicode(testchannel24))
        serviceIdlist.append(unicode(testchannel25))
        serviceIdlist.append(unicode(testchannel26))
        serviceIdlist.append(unicode(testchannel27))
        serviceIdlist.append(unicode(testchannel28))
        serviceIdlist.append(unicode(testchannel29))
        serviceIdlist.append(unicode(testchannel30))
        serviceIdlist.append(unicode(testchannel31))
        serviceIdlist.append(unicode(testchannel32))
        serviceIdlist.append(unicode(testchannel33))
        serviceIdlist.append(unicode(testchannel34))
        serviceIdlist.append(unicode(testchannel35))
        serviceIdlist.append(unicode(testchannel36))
        serviceIdlist.append(unicode(testchannel37))
        serviceIdlist.append(unicode(testchannel38))
        serviceIdlist.append(unicode(testchannel39))
        serviceIdlist.append(unicode(testchannel41))
        serviceIdlist.append(unicode(testchannel42))
        serviceIdlist.append(unicode(testchannel43))
        serviceIdlist.append(unicode(testchannel44))
        serviceIdlist.append(unicode(testchannel45))
        serviceIdlist.append(unicode(testchannel46))
        serviceIdlist.append(unicode(testchannel47))
        serviceIdlist.append(unicode(testchannel48))
        serviceIdlist.append(unicode(testchannel49))
        serviceIdlist.append(unicode(testchannel50))

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
        payload_list = []
        content_list = []
        broadcast_time_dict = {}
        broadcasting_starttime = 0
        ingestion_delay = 120
        map_copy_type = {}
        hh1_content_start_index = 0
        hh1_content_end_index = 1
        hh2_content_start_index = 1
        hh2_content_end_index = 2
        hh3_content_start_index = 2
        hh3_content_end_index = 3
        hh4_content_start_index = 3
        hh4_content_end_index = 4
        recording_delay = 60
        source_region = cfg["recorderRegion"]
        dest_region = cfg["recorderRegion"]

        srt_content = [
                       [source_region, str(testchannel18), dest_region, "common"],
                       [source_region, str(testchannel19), dest_region, "NoChange"],
                       [source_region, str(testchannel20), dest_region, "unique"],
                       [source_region, str(testchannel21), dest_region, "common"],
                       [source_region, str(testchannel22), dest_region, "NoChange"],
                       [source_region, str(testchannel23), dest_region, "unique"],
                       [source_region, str(testchannel24), dest_region, "common"],
                       [source_region, str(testchannel25), dest_region, "NoChange"],
                       [source_region, str(testchannel26), dest_region, "unique"],
                       [source_region, str(testchannel27), dest_region, "common"],
                       [source_region, str(testchannel28), dest_region, "NoChange"],
                       [source_region, str(testchannel29), dest_region, "unique"],
                       [source_region, str(testchannel30), dest_region, "common"],
                       [source_region, str(testchannel31), dest_region, "NoChange"],
                       [source_region, str(testchannel32), dest_region, "unique"],
                       [source_region, str(testchannel33), dest_region, "common"],
                       [source_region, str(testchannel34), dest_region, "NoChange"],
                       [source_region, str(testchannel35), dest_region, "NoChange"],
                       [source_region, str(testchannel36), dest_region, "common"],
                       [source_region, str(testchannel37), dest_region, "NoChange"],
                       [source_region, str(testchannel38), dest_region, "unique"],
                       [source_region, str(testchannel39), dest_region, "common"],
                       [source_region, str(testchannel40), dest_region, "NoChange"],
                       [source_region, str(testchannel41), dest_region, "unique"],
                       [source_region, str(testchannel42), dest_region, "common"],
                       [source_region, str(testchannel43), dest_region, "NoChange"],
                       [source_region, str(testchannel44), dest_region, "unique"],
                       [source_region, str(testchannel45), dest_region, "common"],
                       [source_region, str(testchannel46), dest_region, "NoChange"],
                       [source_region, str(testchannel47), dest_region, "unique"],
                       [source_region, str(testchannel48), dest_region, "common"],
                       [source_region, str(testchannel49), dest_region, "NoChange"],
                       [source_region, str(testchannel50), dest_region, "unique"],
                       [source_region, str(testchannel1), dest_region, "common"],
                       [source_region, str(testchannel2), dest_region, "NoChange"],
                       [source_region, str(testchannel3), dest_region, "unique"],
                       [source_region, str(testchannel4), dest_region, "common"],
                       [source_region, str(testchannel5), dest_region, "NoChange"],
                       [source_region, str(testchannel6), dest_region, "unique"],
                       [source_region, str(testchannel7), dest_region, "common"],
                       [source_region, str(testchannel8), dest_region, "NoChange"],
                       [source_region, str(testchannel9), dest_region, "unique"],
                       [source_region, str(testchannel10), dest_region, "common"],
                       [source_region, str(testchannel11), dest_region, "NoChange"],
                       [source_region, str(testchannel12), dest_region, "unique"],
                       [source_region, str(testchannel13), dest_region, "common"],
                       [source_region, str(testchannel14), dest_region, "NoChange"],
                       [source_region, str(testchannel15), dest_region, "unique"],
                       [source_region, str(testchannel16), dest_region, "common"],
                       [source_region, str(testchannel17), dest_region, "NoChange"], ]

        srt_content_reset = [[source_region, "*", dest_region, "NoChange"], ]

        copy_index_srt = 3
        channel_index_srt = 1
        booking_copy_type = "UNIQUE"

        # Do PPS Booking
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        ###########################  USER DEFINED POST TIME IN UTC ############
        start_delay = 5
        timeslotinminutes = cfg["test_channels"]["longProgramLength"] * 4
        ingestion_time = get_utc_time_after_n_minutes(start_delay, True)
        start_time = datetime.datetime.strptime(
            ingestion_time, '%Y-%m-%dT%H:%M:%S')
        post_time = calendar.timegm(start_time.timetuple()) + 0.0001
        #######################################################################

        print "### STEP1: Ingest an events of n minutes with the posttime "\
            "of n Minutes to the CI Host on 50 channels. ######## \n \n"
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']

        eventtitle1 = "commoncp" + str(random.randint(1, 499))

        channel1 = ChannelLineup(BoundaryInMinutes=0)
        channel1.add_to_lineup(
            serviceId=testchannel1,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel1.postXmlData(ci_host, ci_port, startTime=post_time)
        channel1.writeXmlFiles(startTime=post_time)

        print "channel1 : ", channel1

        channel2 = ChannelLineup(BoundaryInMinutes=0)
        channel2.add_to_lineup(
            serviceId=testchannel2,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel2.postXmlData(ci_host, ci_port, startTime=post_time)
        channel2.writeXmlFiles(startTime=post_time)

        print "channel2 : ", channel2

        channel3 = ChannelLineup(BoundaryInMinutes=0)
        channel3.add_to_lineup(
            serviceId=testchannel3,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel3.postXmlData(ci_host, ci_port, startTime=post_time)
        channel3.writeXmlFiles(startTime=post_time)

        print "channel3 : ", channel3

        channel4 = ChannelLineup(BoundaryInMinutes=0)
        channel4.add_to_lineup(
            serviceId=testchannel4,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel4.postXmlData(ci_host, ci_port, startTime=post_time)
        channel4.writeXmlFiles(startTime=post_time)

        print "channel4 : ", channel4

        channel5 = ChannelLineup(BoundaryInMinutes=0)
        channel5.add_to_lineup(
            serviceId=testchannel5,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel5.postXmlData(ci_host, ci_port, startTime=post_time)
        channel5.writeXmlFiles(startTime=post_time)

        print "channel5 : ", channel5

        channel6 = ChannelLineup(BoundaryInMinutes=0)
        channel6.add_to_lineup(
            serviceId=testchannel6,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel6.postXmlData(ci_host, ci_port, startTime=post_time)
        channel6.writeXmlFiles(startTime=post_time)

        print "channel6 : ", channel6

        channel7 = ChannelLineup(BoundaryInMinutes=0)
        channel7.add_to_lineup(
            serviceId=testchannel7,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel7.postXmlData(ci_host, ci_port, startTime=post_time)
        channel7.writeXmlFiles(startTime=post_time)

        print "channel7 : ", channel7

        channel8 = ChannelLineup(BoundaryInMinutes=0)
        channel8.add_to_lineup(
            serviceId=testchannel8,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel8.postXmlData(ci_host, ci_port, startTime=post_time)
        channel8.writeXmlFiles(startTime=post_time)

        print "channel8 : ", channel8

        channel9 = ChannelLineup(BoundaryInMinutes=0)
        channel9.add_to_lineup(
            serviceId=testchannel9,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel9.postXmlData(ci_host, ci_port, startTime=post_time)
        channel9.writeXmlFiles(startTime=post_time)

        print "channel9 : ", channel9

        channel10 = ChannelLineup(BoundaryInMinutes=0)
        channel10.add_to_lineup(
            serviceId=testchannel10,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel10.postXmlData(ci_host, ci_port, startTime=post_time)
        channel10.writeXmlFiles(startTime=post_time)

        print "channel10 : ", channel10

        channel11 = ChannelLineup(BoundaryInMinutes=0)
        channel11.add_to_lineup(
            serviceId=testchannel11,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel11.postXmlData(ci_host, ci_port, startTime=post_time)
        channel11.writeXmlFiles(startTime=post_time)

        print "channel11 : ", channel11

        channel12 = ChannelLineup(BoundaryInMinutes=0)
        channel12.add_to_lineup(
            serviceId=testchannel12,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel12.postXmlData(ci_host, ci_port, startTime=post_time)
        channel12.writeXmlFiles(startTime=post_time)

        print "channel12 : ", channel12

        channel13 = ChannelLineup(BoundaryInMinutes=0)
        channel13.add_to_lineup(
            serviceId=testchannel13,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel13.postXmlData(ci_host, ci_port, startTime=post_time)
        channel13.writeXmlFiles(startTime=post_time)

        print "channel13 : ", channel13

        channel14 = ChannelLineup(BoundaryInMinutes=0)
        channel14.add_to_lineup(
            serviceId=testchannel14,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel14.postXmlData(ci_host, ci_port, startTime=post_time)
        channel14.writeXmlFiles(startTime=post_time)

        print "channel14 : ", channel14

        channel15 = ChannelLineup(BoundaryInMinutes=0)
        channel15.add_to_lineup(
            serviceId=testchannel15,
            timeSlotLengthMinutes=timeslotinminutes,
            timeSlotCount=1,
            programIDPrefix=eventtitle1)
        channel15.postXmlData(ci_host, ci_port, startTime=post_time)
        channel15.writeXmlFiles(startTime=post_time)

        print "channel15 : ", channel15

        print "Wait time for the catalog ingest to get synced "\
        "with the CI Host in seconds: " + str(ingestion_delay)
        time.sleep(ingestion_delay)

    except BaseException:
        message = "Testcase Failed: Error Occurred in Configuration " + \
            PrintException(True)
        print message
        tims_dict = update_tims_data(
            tims_dict, 1, message, [
                test_id, test_id2,
                test_id3, test_id4])
        return tims_dict

    for (cmdc_host, pps_host) in hostlist:
        try:

            print "### STEP2: Setting the SRT table in such a way "\
            "to record the contents with specific copy type from the "\
            "concerned channels. ###### \n \n"
            configureSRT_instance = ConfigureSRT()
            configureSRT_instance.modify_srt(cfg, srt_content)

            for householdid in householdid_list:
                cleanup_household(
                    cfg,
                    pps_port,
                    protocol,
                    pps_host,
                    householdid,
                    pps_headers,
                    timeout)

            print "### STEP3: Fetching the grid response to "\
            "collect the ingested content. ##### \n \n"
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
            print "ContentID dictionary from the Grid Response\n" + str(contentId_dict_all)
            assert contentId_dict_all, "Testcase Failed: Unable to "\
            "Form ContentId dictionary from the Grid Response"

            contentId_list = sorted(
                contentId_dict_all.items(),
                key=lambda x: x[1])
            print "ContentId list after Sorting\n" + str(contentId_list)
            assert (len(contentId_list) >
                    0), "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
            print "len(contentId_list) : ", len(contentId_list)

            content_ev1 = contentId_list[0][0]
            content_ev2 = contentId_list[1][0]
            content_ev3 = contentId_list[2][0]
            content_ev4 = contentId_list[3][0]
            content_ev5 = contentId_list[4][0]
            content_ev6 = contentId_list[5][0]
            content_ev7 = contentId_list[6][0]
            content_ev8 = contentId_list[7][0]
            content_ev9 = contentId_list[8][0]
            content_ev10 = contentId_list[9][0]
            content_ev11 = contentId_list[10][0]
            content_ev12 = contentId_list[11][0]
            content_ev13 = contentId_list[12][0]
            content_ev14 = contentId_list[13][0]
            content_ev15 = contentId_list[14][0]

            content_list.append(content_ev1)
            content_list.append(content_ev2)
            content_list.append(content_ev3)
            content_list.append(content_ev4)
            content_list.append(content_ev5)
            content_list.append(content_ev6)
            content_list.append(content_ev7)
            content_list.append(content_ev8)
            content_list.append(content_ev9)
            content_list.append(content_ev10)
            content_list.append(content_ev11)
            content_list.append(content_ev12)
            content_list.append(content_ev13)
            content_list.append(content_ev14)
            content_list.append(content_ev15)

            copy_type = [copy_type[copy_index_srt]
                         for copy_type in srt_content]
            chanel_map = [channel_map[channel_index_srt]
                          for channel_map in srt_content]
            for channel, copy_type in zip(chanel_map, copy_type):
                map_copy_type.update({channel: copy_type})

            print "map_copy_type : ", map_copy_type

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

            payload_ev3 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev3)

            payload_ev4 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev4)

            payload_ev5 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev5)

            payload_ev6 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev6)

            payload_ev7 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev7)

            payload_ev8 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev8)

            payload_ev9 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev9)

            payload_ev10 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev10)

            payload_ev11 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev11)

            payload_ev12 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev12)

            payload_ev13 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev13)

            payload_ev14 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev14)

            payload_ev15 = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR"
                            }""" % (content_ev15)

            payload_list.append(payload_ev1)
            payload_list.append(payload_ev2)
            payload_list.append(payload_ev3)
            payload_list.append(payload_ev4)
            payload_list.append(payload_ev5)
            payload_list.append(payload_ev6)
            payload_list.append(payload_ev7)
            payload_list.append(payload_ev8)
            payload_list.append(payload_ev9)
            payload_list.append(payload_ev10)
            payload_list.append(payload_ev11)
            payload_list.append(payload_ev12)
            payload_list.append(payload_ev13)
            payload_list.append(payload_ev14)
            payload_list.append(payload_ev15)

            print "About to start the event 1 booking\n\n"
            print "### STEP4: Perform PPS event booking from "\
                "all four households. ##### \n \n"
            for householdid in householdid_list[:1]:
                for content_ev1, payload_ev1 in zip(
                        content_list[hh1_content_start_index:hh1_content_end_index],\
                        payload_list[hh1_content_start_index:hh1_content_end_index]):
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
                            tims_dict, 1, message, [test_id, test_id2, test_id3, test_id4])

            for householdid in householdid_list[1:2]:
                for content_ev1, payload_ev1 in zip(
                        content_list[hh2_content_start_index:hh2_content_end_index],\
                        payload_list[hh2_content_start_index:hh2_content_end_index]):
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
                            tims_dict, 1, message, [test_id, test_id2, test_id3, test_id4])

            for householdid in householdid_list[2:3]:
                for content_ev1, payload_ev1 in zip(
                        content_list[hh3_content_start_index:hh3_content_end_index], \
                        payload_list[hh3_content_start_index:hh3_content_end_index]):
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
                            tims_dict, 1, message, [test_id, test_id2, test_id3, test_id4])

            for householdid in householdid_list[3:]:
                for content_ev1, payload_ev1 in zip(
                        content_list[hh4_content_start_index:hh4_content_end_index], \
                        payload_list[hh4_content_start_index:hh4_content_end_index]):
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
                            tims_dict, 1, message, [test_id, test_id2, test_id3, test_id4])

            print "PPS Booking is successful for the event contentid ",\
            content_list, " on all 4 households"

            print "### STEP5: Confirming that all four households "\
            "has its booked items in booked state. ##### \n \n"
            time.sleep(fetch_bookingcatalog_delay)
            time.sleep(60)
            # Getting Catalog Response for the Booked Catalog
            for householdid in householdid_list[:1]:
                for content_ev1, payload_ev1 in zip(
                        content_list[hh1_content_start_index:hh1_content_end_index],\
                        payload_list[hh1_content_start_index:hh1_content_end_index]):
                    catalogresult, catalogresponse = verify_booking(
                        pps_port, protocol, pps_host, householdid, content_ev1, timeout)
                    print "Booking response :", catalogresult
                    if catalogresult == "PASS":
                        jsonresponse = json.loads(catalogresponse.content)
                        for items in jsonresponse:
                            try:
                                if items['scheduleInstance'] == content_ev1:
                                    broadcasting_starttime = items['content']['broadcastDateTime']
                                    broadcast_time_dict.update(
                                        {content_ev1: broadcasting_starttime})
                            except BaseException:
                                pass
                    else:
                        message = "TestCase  Failed : Content ID " + \
                            str(content_ev1) + " in household " + \
                            str(householdid) + " is not in the BOOKED state"
                        assert False, message

            for householdid in householdid_list[1:2]:
                for content_ev1, payload_ev1 in zip(
                        content_list[hh2_content_start_index:hh2_content_end_index], \
                        payload_list[hh2_content_start_index:hh2_content_end_index]):
                    catalogresult, catalogresponse = verify_booking(
                        pps_port, protocol, pps_host, householdid, content_ev1, timeout)
                    print "Booking response :", catalogresult
                    if catalogresult == "PASS":
                        jsonresponse = json.loads(catalogresponse.content)
                        for items in jsonresponse:
                            try:
                                if items['scheduleInstance'] == content_ev1:
                                    broadcasting_starttime = items['content']['broadcastDateTime']
                                    broadcast_time_dict.update(
                                        {content_ev1: broadcasting_starttime})
                            except BaseException:
                                pass
                    else:
                        message = "TestCase  Failed : Content ID " + \
                            str(content_ev1) + " in household " + \
                            str(householdid) + " is not in the BOOKED state"
                        assert False, message

            for householdid in householdid_list[2:3]:
                for content_ev1, payload_ev1 in zip(
                        content_list[hh3_content_start_index:hh3_content_end_index],\
                        payload_list[hh3_content_start_index:hh3_content_end_index]):
                    catalogresult, catalogresponse = verify_booking(
                        pps_port, protocol, pps_host, householdid, content_ev1, timeout)
                    print "Booking response :", catalogresult
                    if catalogresult == "PASS":
                        jsonresponse = json.loads(catalogresponse.content)
                        for items in jsonresponse:
                            try:
                                if items['scheduleInstance'] == content_ev1:
                                    broadcasting_starttime = items['content']['broadcastDateTime']
                                    broadcast_time_dict.update(
                                        {content_ev1: broadcasting_starttime})
                            except BaseException:
                                pass
                    else:
                        message = "TestCase  Failed : Content ID " + \
                            str(content_ev1) + " in household " + \
                            str(householdid) + " is not in the BOOKED state"
                        assert False, message

            for householdid in householdid_list[3:]:
                for content_ev1, payload_ev1 in zip(
                        content_list[hh4_content_start_index:hh4_content_end_index], \
                        payload_list[hh4_content_start_index:hh4_content_end_index]):
                    catalogresult, catalogresponse = verify_booking(
                        pps_port, protocol, pps_host, householdid, content_ev1, timeout)
                    print "Booking response :", catalogresult
                    if catalogresult == "PASS":
                        jsonresponse = json.loads(catalogresponse.content)
                        for items in jsonresponse:
                            try:
                                if items['scheduleInstance'] == content_ev1:
                                    broadcasting_starttime = items['content']['broadcastDateTime']
                                    broadcast_time_dict.update(
                                        {content_ev1: broadcasting_starttime})
                            except BaseException:
                                pass
                    else:
                        message = "TestCase  Failed : Content ID " + \
                            str(content_ev1) + " in household " \
                            + str(householdid) + " is not in the BOOKED state"
                        assert False, message
            print "broadcast_time_dict : ", broadcast_time_dict

            broadcasting_starttime = timeDiff(
                broadcast_time_dict[content_list[0]])

            recordingstatechage = recordingstatecheck_timedelay + broadcasting_starttime
            print "Script will wait for " + str(recordingstatechage / 60) \
            + " minutes to check the event recording state"
            time.sleep(recordingstatechage)
            print "Waiting additional %s seconds to workaround the\
            state change issue." % (recording_delay)
            time.sleep(recording_delay)
            time.sleep(recording_delay)
            time.sleep(recording_delay)
            time.sleep(recording_delay)

            print "### STEP6: Confirming that all four households has "\
            "its booked items in recording state. ##### \n \n"
            for householdid in householdid_list[:1]:
                for content_ev1 in content_list[hh1_content_start_index:hh1_content_end_index]:
                    recordingcatalogresult = verify_recording_state(
                        pps_port, protocol, pps_host, householdid, content_ev1, timeout)[0]
                    if recordingcatalogresult != "PASS":
                        message = "Testcase Failed: Content ID {0} "\
                        "in household {1} is not in the RECORDING state".format(
                            content_ev1, householdid)
                        assert False, message

            for householdid in householdid_list[1:2]:
                for content_ev1 in content_list[hh2_content_start_index:hh2_content_end_index]:
                    recordingcatalogresult = verify_recording_state(
                        pps_port, protocol, pps_host, householdid, content_ev1, timeout)[0]
                    if recordingcatalogresult != "PASS":
                        message = "Testcase Failed: Content ID {0} in household "\
                        "{1} is not in the RECORDING state".format(
                            content_ev1, householdid)
                        assert False, message

            for householdid in householdid_list[2:3]:
                for content_ev1 in content_list[hh3_content_start_index:hh3_content_end_index]:
                    recordingcatalogresult = verify_recording_state(
                        pps_port, protocol, pps_host, householdid, content_ev1, timeout)[0]
                    if recordingcatalogresult != "PASS":
                        message = "Testcase Failed: Content ID {0} "\
                        "in household {1} is not in the RECORDING state".format(
                            content_ev1, householdid)
                        assert False, message

            for householdid in householdid_list[3:]:
                for content_ev1 in content_list[hh4_content_start_index:hh4_content_end_index]:
                    recordingcatalogresult = verify_recording_state(
                        pps_port, protocol, pps_host, householdid, content_ev1, timeout)[0]
                    if recordingcatalogresult != "PASS":
                        message = "Testcase Failed: Content ID {0} in household {1} is not in the RECORDING state".format(
                            content_ev1, householdid)
                        assert False, message

            print "### STEP7: Confirming that all households, recording its content with "\
                "specific copy type set per static_route_table. ##### \n \n"
            # TODO: Verify SRT is being reflected in Riodev.

            for content_ev1 in content_list[hh1_content_start_index:hh1_content_end_index]:

                playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol,\
                                   [content_ev1], householdid_list[:1], timeout)
                print "Playback URI list :", playbackuri_list
                contentidlist = get_contentid_from_recid(
                    cfg, playbackuri_list, timeout)
                print "ContentId list :", contentidlist
                vmr_response_1 = get_vmr_response(
                    cfg, contentidlist[0], timeout)
                riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
                streamid = riodev_recording_hh1["StreamID"]
                if not isinstance(streamid, str):
                    copy_type = map_copy_type[str(streamid)]
                else:
                    copy_type = map_copy_type[streamid]
                if copy_type == "NoChange":
                    copy_type = booking_copy_type
                copy_type = copy_type.upper()

                print "copy_type : ", copy_type
                print "riodev_recording_hh1 : ", riodev_recording_hh1
                assert riodev_recording_hh1["CopyType"] == copy_type, \
                "Testcase Failed: Content %s are not in expected copy type %s in household 1." % (
                    content_ev1, copy_type)

            print "\n" * 5

            for content_ev1 in content_list[hh2_content_start_index:hh2_content_end_index]:

                playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol,\
                                   [content_ev1], householdid_list[1:2], timeout)
                print "Playback URI list :", playbackuri_list
                contentidlist = get_contentid_from_recid(
                    cfg, playbackuri_list, timeout)
                print "ContentId list :", contentidlist
                vmr_response_1 = get_vmr_response(
                    cfg, contentidlist[0], timeout)
                riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
                streamid = riodev_recording_hh1["StreamID"]
                if not isinstance(streamid, str):
                    copy_type = map_copy_type[str(streamid)]
                else:
                    copy_type = map_copy_type[streamid]
                if copy_type == "NoChange":
                    copy_type = booking_copy_type
                copy_type = copy_type.upper()

                print "copy_type : ", copy_type
                print "riodev_recording_hh1 : ", riodev_recording_hh1
                assert riodev_recording_hh1["CopyType"] == copy_type, \
                "Testcase Failed: Content %s are not in expected copy type %s in household 2." % (
                    content_ev1, copy_type)

            print "\n" * 5

            for content_ev1 in content_list[hh3_content_start_index:hh3_content_end_index]:

                playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol,\
                                   [content_ev1], householdid_list[2:3], timeout)
                print "Playback URI list :", playbackuri_list
                contentidlist = get_contentid_from_recid(
                    cfg, playbackuri_list, timeout)
                print "ContentId list :", contentidlist
                vmr_response_1 = get_vmr_response(
                    cfg, contentidlist[0], timeout)
                riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
                streamid = riodev_recording_hh1["StreamID"]
                if not isinstance(streamid, str):
                    copy_type = map_copy_type[str(streamid)]
                else:
                    copy_type = map_copy_type[streamid]
                if copy_type == "NoChange":
                    copy_type = booking_copy_type
                copy_type = copy_type.upper()

                print "copy_type : ", copy_type
                print "riodev_recording_hh1 : ", riodev_recording_hh1
                assert riodev_recording_hh1["CopyType"] == copy_type, \
                "Testcase Failed: Content %s are not in expected copy type %s in household 3." % (
                    content_ev1, copy_type)

            print "\n" * 5

            for content_ev1 in content_list[hh4_content_start_index:hh4_content_end_index]:

                playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, \
                                   [content_ev1], householdid_list[3:], timeout)
                print "Playback URI list :", playbackuri_list
                contentidlist = get_contentid_from_recid(
                    cfg, playbackuri_list, timeout)
                print "ContentId list :", contentidlist
                vmr_response_1 = get_vmr_response(
                    cfg, contentidlist[0], timeout)
                riodev_recording_hh1 = json.loads(vmr_response_1.content)[0]
                streamid = riodev_recording_hh1["StreamID"]
                if not isinstance(streamid, str):
                    copy_type = map_copy_type[str(streamid)]
                else:
                    copy_type = map_copy_type[streamid]
                if copy_type == "NoChange":
                    copy_type = booking_copy_type
                copy_type = copy_type.upper()

                print "copy_type : ", copy_type
                print "riodev_recording_hh1 : ", riodev_recording_hh1
                assert riodev_recording_hh1["CopyType"] == copy_type, \
                "Testcase Failed: Content %s are not in expected copy type %s in household 4." % (
                    content_ev1, copy_type)

            print "\n" * 5
            print "Contents are getting recorded in expected copy type in all households."

            message = "TestCase Passed : SRT is working as expected."
            tims_dict = update_tims_data(
                tims_dict, 0, message, [
                    test_id, test_id2,
                    test_id3, test_id4])

        except AssertionError as ae:
            message = str(ae)
            tims_dict = update_tims_data(
                tims_dict, 1, message, [
                    test_id, test_id2,
                    test_id3, test_id4])

        except Exception as e:
            message = str(e)
            tims_dict = update_tims_data(
                tims_dict, 1, message, [
                    test_id, test_id2,
                    test_id3, test_id4])

        finally:
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
