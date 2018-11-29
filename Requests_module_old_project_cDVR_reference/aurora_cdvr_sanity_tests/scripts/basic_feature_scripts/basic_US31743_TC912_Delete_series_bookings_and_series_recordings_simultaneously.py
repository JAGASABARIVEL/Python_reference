#!/usr/bin/python
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
from os.path import isfile
from genChannelLineup import *
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
######################################################################################################
# Test Steps:Delete series bookings and series recordings simultaneously
# STEP1:Ingest a catalog for 1 series having 3 episode of n min with the time gap inbetween each episodes
# STEP2:Getting the ContentId List for all the series and doing the booking
# STEP3:Checking all the episodes of the series in the booking catalog and getting the neccessary details
# STEP4:Fetch the Recorded library once the first episode recording has started
# STEP5:Fetch the Recorded library once the second episode's recording has started
# STEP6:Delete the Booking and Recording simultaneously and verifying it in the booking catalog and recorded library
######################################################################################################
def doit(cfg,printflg=False):
    try :
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg,printflg)
        end_time = time.time()
        time_value = end_time - start_time
        time_value = round(time_value , 6 )
        time_value = str(time_value)
        filename =  cfg['test_results']['filename']
        data = {
            "config": {
                "labname" : cfg['LABNAME'] ,
                "extraconf" : str(cfg['EXTRACONF']) ,
                "gitrepo" : cfg['GITREPO'] ,
                "gitlastcommit" :  cfg['GITLASTCOMMIT'] ,
                "description" : cfg['lab-description']
               }
            }
        timsResults = JsonReadWrite(filename)
        timsResults.writeDictJson(data)
        status_value = []
        for key,val in dict.items(rc):
            TC = key
            US = val[0]
            message = val[1]
            status_value.append(val[2])
            if val[2] == 0 or val[2] == 2:
                status = "PASS"
            elif val[2] == 3:
                status = "Not Run"
            elif val[2] == 4:
                status = "Unsupported"
            else:
                status = "FAIL"
            name  =  os.path.basename(__file__)[:-3]
            # message will eventually be the last log message but this is a proof of concept
            results = {
                "CF": "",
                "I": "Core DVR Functionality",
                "MF": "",
                "TC": TC,
                "US": US,
                "message": message,
                "name": name,
                "status": status,
                "time": time_value
                }
            timsResults.appendListToKey('testsuite:basic-feature', results)
        if status_value :
            if ( 1 in status_value ) or ( 3 in status_value) :
                return (1)
            elif (4 in status_value) or (2 in status_value):
                return (2)
            else :
                return (0)
        else :
             print "status_value not present "
             return 1
    except:
        print "Error Occurred in Script \n"
        PrintException()
        return (1)

def doit_wrapper(cfg,printflg=False):
    try:
        message = ""
        status = 3
        tims_dict = {
            "TC912": ["US31743", message, status],
            "TC880": ["US31773", message, status]
        }
        print "\n US31743: Delete series recording"
        print "\n TC912: Delete series bookings and series recordings simultaneously"
        print "\n TC880: Delete series bookings and series recordings simultaneously"
        
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        #Initialize the Variables
        index = 0
        timeout = 2 
        serviceIdlist = []
        random_contentId = None
        gridservicelistresponse =None
        contentId_dict_all =None
        jsonbookedcatalog =None
        recorded_lib_json =None
        recorded_lib =None
        i=0
        episode_count = 0
        episode_broadcast_time = {}
        episode_end_time= {}
        episode_contentid = {}
        episode_uri = {}
        booked_episodelist = []
        booked_list = []
        contentId_list = []

        # set values based on config
        upm_host = cfg['upm']['host']
        pps_hosts = [cfg['pps']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        households_needed = cfg['basic_feature']['households_needed']
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        series_bookingstatecheck = cfg['pps']['series_bookingstatecheck_waittime']
        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceIdlist.append(unicode(testchannel1))
        prefix = cfg['basic_feature']['household_prefix']
        cmdc_headers = {
            'Accept': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        hostlist = list(itertools.product(cmdc_hosts,pps_hosts))

        #Late post time such that series recording do not start

        print "### STEP1:Ingest a catalog for 1 series having 3 episode of n min with the time gap inbetween each episodes################################################## \n \n "
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        testchannel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        title = 'Delseries' + str(random.randint(500,599))
        channel1 = ChannelLineup(BoundaryInMinutes=0)
        timeslotinminutes = cfg['test_channels']['mediumProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        channel1.add_to_lineup(serviceId=testchannel1,timeSlotLengthMinutes=timeslotinminutes,showID=title,startEpisodeNumber=1,episodeCount=1, timeSlotCount=1)
        end_time1 = channel1.postXmlData(ci_host,ci_port,startTime = post_time)
        end_time1 = int(end_time1) + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule'])
        print channel1
        channel2 = ChannelLineup(BoundaryInMinutes=0)
        channel2.add_to_lineup(serviceId=testchannel1,timeSlotLengthMinutes=timeslotinminutes,showID=title,startEpisodeNumber=2,episodeCount=1, timeSlotCount=1)
        end_time2 = channel2.postXmlData(ci_host,ci_port,startTime = end_time1)
        end_time2 = int(end_time2) + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule'])
        print channel2
        channel3 = ChannelLineup(BoundaryInMinutes=0)
        channel3.add_to_lineup(serviceId=testchannel1,timeSlotLengthMinutes=timeslotinminutes,showID=title,startEpisodeNumber=3,episodeCount=1, timeSlotCount=1)
        channel3.postXmlData(ci_host,ci_port,startTime = end_time2)
        print channel3
        length1 =  channel1.getTotalLength()
        length2 =  channel2.getTotalLength()
        length3 =  channel3.getTotalLength()
        length = length1 + length2 + length3
        sleep_time = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_time)
        time.sleep(sleep_time)
    except:
        message =  "Testcase Failed: Error Occurred in Configuration " + PrintException(True) 
        print  message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC912","TC880"])
        return tims_dict
    try:
        for (cmdc_host,pps_host) in hostlist:
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            print "### STEP2:Getting the ContentId List for all the series and doing the booking ############################################# \n \n "
            gridservicelistresponse = fetch_gridRequest(catalogueId,protocol,cmdc_host,cmdc_port,serviceIdlist,region,timeout,printflg)
            if gridservicelistresponse:
                contentId_dict_all = get_series_contentIddict_bytitle(gridservicelistresponse,title,['title','seriesId','episodeNumber'])
                print "Series ContentId dictionary from the grid response\n" + str(contentId_dict_all)
                if contentId_dict_all :
                    series_contentId = sorted(contentId_dict_all.items(), key=lambda x:x[1])
                    print "Series ContentId list after sorting\n" +str(series_contentId)
                    if len(series_contentId) > 2:
                        for items in series_contentId:
                            contentId_list.append(items[0])
                        random_contentId = series_contentId[0][0]
                        seriesId = series_contentId[0][1][3]
                        print contentId_list
                        payload = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true, 
                            "pvr":"nPVR",
                            "recurrence":"SERIES"
                            }""" % (random_contentId)
                        result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,payload,random_contentId,timeout,printflg)
                        if result == "PASS":
                            print "PPS booking is successful for the event contentId %s"%random_contentId
                            time.sleep(series_bookingstatecheck)
                        else:
                            message = "Testcase Failed: PPS Booking failed for the event contentId %s" %(random_contentId)
                            print  message
                            tims_dict = update_tims_data(tims_dict,1, message, ["TC912","TC880"])
                            return tims_dict
                    else:
                        message = "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                        print  message
                        tims_dict = update_tims_data(tims_dict,1, message, ["TC912","TC880"])
                        return tims_dict                    
                else:
                    message ="Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    print  message
                    tims_dict = update_tims_data(tims_dict, 1, message, ["TC912","TC880"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Fetch Grid Response"
                print  message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC912","TC880"])
                return tims_dict

            print "###STEP3:Checking all the episodes of all the series in the booking catalog and getting the neccessary details#################### \n \n"
            jsonbookedcatalog = fetch_bookingCatalog(pps_port,protocol,pps_host,householdid,timeout)
            if jsonbookedcatalog:
                episodes = booked_episodes(seriesId, jsonbookedcatalog)
                print "Series Episodes in the booked catalog %s" % episodes
                if episodes:
                    episode_detail = episodes.values()
                    episode_numbers = episodes.keys()
                    if len(episode_numbers) > 2:
                        printLog("Episode numbers of the series in the booked catalog" + str(episode_numbers), printflg)
                        for key,value in episodes.iteritems():
                            booked_contentID = value[6]
                            booked_episodelist.append(booked_contentID)
                        print "List of Booked Episodes for seriesID: ", seriesId, " -> " , episodes                    
                    else:
                        message = "Testcase Failed: Count of Episodes is not much as expected"
                        debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                        print  message
                        tims_dict = update_tims_data(tims_dict, 1, message, ["TC912","TC880"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to Fetch Booked Episodes"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    print  message
                    tims_dict = update_tims_data(tims_dict, 1, message, ["TC912","TC880"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to fetch Booked Catalog"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print  message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC912","TC880"])
                return tims_dict
            print "\nList of Episodes booked: ", booked_episodelist
            num_of_booked = 0
            for ids in contentId_list:
                 if ids in booked_episodelist:
                     num_of_booked = num_of_booked + 1
            if num_of_booked == len(contentId_list):
                print "All the episodes are present in Booked catalog"
            else:
                message = "Testcase Failed: All episodes are not booked successfully"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print  message
                tims_dict = update_tims_data(tims_dict,1, message, ["TC912","TC880"])
                return tims_dict
            
            # Episodes details
            for numbers in episode_numbers:
                episode_broadcast_time[i] = episode_detail[i][0]
                episode_end_time[i] = episode_detail[i][1]
                episode_contentid[i] = episode_detail[i][6]
                episode_uri[i] = episode_detail[i][4]
                i = i + 1
            first_pgm_start_time = get_timedifference(episode_broadcast_time[0], printflg)
            first_pgm_end_time = get_timedifference(episode_end_time[0], printflg)
            second_pgm_start_time = get_timedifference(episode_broadcast_time[1], printflg)
            second_pgm_end_time = get_timedifference(episode_end_time[1], printflg)
            last_pgm_end_time = get_timedifference(episode_end_time[2], printflg)
            first_episode_contentid = episode_contentid[0]
            second_episode_contentid = episode_contentid[1]
            first_episode_uri = episode_uri[0]

            print "###STEP4:Fetch the Recorded library once the first episode recording has started######################################################## \n \n"
            print "Wait time for the system to start recording first episode is" + str(first_pgm_start_time) + "Seconds"
            time.sleep(first_pgm_start_time)
            time.sleep(recordingstatecheck_waittime)
            time.sleep(recordingstatecheck_waittime) #Additional delay for state change issue
            time.sleep(recordingstatecheck_waittime) #Additional delay for state change issue
            count1 = 0
            recordingcatalogresult,recording_lib_json = verify_recording_state(pps_port,protocol,pps_host,householdid,random_contentId,timeout)
            if recordingcatalogresult == "PASS" and recording_lib_json:
                print "Wait time for the system to start recording second episode is " + str(second_pgm_start_time) + " Seconds"
                time.sleep(second_pgm_start_time)
                time.sleep(recordingstatecheck_waittime)
                time.sleep(recordingstatecheck_waittime)#Additional delay for state change issue
                time.sleep(recordingstatecheck_waittime)#Additional delay for state change issue
            else:
                message = "Testcase Failed: Unable to Verify Recording Catalog"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC912","TC880"])
                return tims_dict

            print "###STEP5:Fetch the Recorded library once the second episode's recording has started################################### \n \n"
            recordedcatalogresult,recorded_lib_json = verify_recorded_state(pps_port,protocol,pps_host,householdid,first_episode_contentid,timeout)
            recordingcatalogresult1,recordingcatalogresponse1 = verify_recording_state(pps_port,protocol,pps_host,householdid,second_episode_contentid,timeout)
            if recordedcatalogresult == "PASS" and recordingcatalogresult1 == "PASS":
                print "First Episode completed recording and second episode is in recording state"
            else:
                message = "Testcase Failed: Unable to Verify Recorded Catalog"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                print  message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC912","TC880"])
                return tims_dict

            print "###STEP6:Delete the Booking and Recording simultaneously and verifying it in the booking catalog and recorded library #################### \n \n "
            check_count = 0
            deletePPSrecordingresult = delete_seriesrecordings(pps_port,protocol,pps_host,pps_headers,timeout,first_episode_uri,printflg=False)
            if deletePPSrecordingresult == "PASS":
                jsonbookedcatalog = fetch_bookingCatalog(pps_port, protocol, pps_host, householdid, timeout)
                if jsonbookedcatalog:
                    episodes = booked_episodes(seriesId, jsonbookedcatalog)
                    print "Booked Episodes %s" % episodes
                    if episodes:
                        episode_detail = episodes.values()
                        episode_numbers = episodes.keys()
                        printLog("Episode numbers of the series in the booked catalog" + str(episode_numbers), printflg)
                        for key,value in episodes.iteritems():
                            booked_contentID = value[6]
                            booked_list.append(booked_contentID)
                        print "List of Booked Episodes for seriesID: ", seriesId, " -> " , episodes
                        print "\nList of Episodes booked: ", booked_list
                        for ids in contentId_list:
                            if ids in booked_list:
                                check_count = check_count + 1
                    if check_count:
                        message = "Testcase Failed: Booked Episodes are not deleted from the booked catalog"
                        debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,1, message, ["TC912","TC880"])
                        return tims_dict
                    else:
                        print "Booked Episodes are deleted from the booked catalog"
                        count3 = 0
                        recorded_lib_json = fetch_recordingCatalog(pps_port,protocol,pps_host,householdid,timeout)
                        if recorded_lib_json:
                            recorded_lib = json.loads(recorded_lib_json.content)
                            for val in recorded_lib:
                                try:
                                   for value in contentId_list:
                                       if val['scheduleInstance'] == value :
                                           count3 = count3 + 1
                                except: 
                                    pass
                            if count3 == 0:
                                message= "Testcase Passed: Booked and Recorded Episodes are deleted from the library simultaneously"
                                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,0, message, ["TC912","TC880"])
                                return tims_dict
                            else:
                                message = "Testcase Failed: Recorded Episodes are not deleted from the Recorded library"
                                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,1, message, ["TC912","TC880"])
                                return tims_dict
                        else:
                            message = "Testcase Failed: Unable to fetch Recorded Catalog"
                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                            print  message
                            tims_dict = update_tims_data(tims_dict,1, message, ["TC912","TC880"])
                            return tims_dict
                else:
                    print "Booked Episodes are deleted from the booked catalog successfully"
                    recorded_lib_json = fetch_recordingCatalog(pps_port,protocol,pps_host,householdid,timeout)
                    count3 = 0
                    if recorded_lib_json:
                        recorded_lib = json.loads(recorded_lib_json.content)
                        for val in recorded_lib:
                            try:
                                for value in contentId_list:
                                    if val['scheduleInstance'] == value :
                                        count3 = count3 + 1
                            except:
                                pass
                        if count3 == 0:
                            message = "Testcase Passed: Booked and Recorded Episodes are deleted from the library simultaneously"
                            cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                            print  message
                            tims_dict = update_tims_data(tims_dict,0, message, ["TC912","TC880"])
                            return tims_dict
                        else:
                            message = "Testcase Failed: Recorded Episodes are not deleted from the Recorded library"
                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                            print  message
                            tims_dict = update_tims_data(tims_dict,1, message, ["TC912","TC880"])
                            return tims_dict
                    else:
                        message = "Testcase Failed: Unable to fetch Recorded Catalog"
                        debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                        print  message
                        tims_dict = update_tims_data(tims_dict,1, message, ["TC912","TC880"])
                        return tims_dict
            else:
                message = "Testcase Failed: Unable to Delete the Booked and Recorded Episodes"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1, message, ["TC912","TC880"])
                return tims_dict
    except:
        message =  "Testcase Failed: Error Occurred in Script " + PrintException(True)
        debug_print_log(pps_port,protocol,pps_host,householdid,timeout) 
        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
        print  message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC912","TC880"])
        return tims_dict
          
 
if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    #read config file
    sa = sys.argv
    cfg = relative_config_file(sa,scriptName)
    if cfg['basic_feature']['print_cfg']:
         print "\nThe following configuration is being used:\n"
         pprint(cfg)
         print
    L = doit_wrapper(cfg, True)
    status_value = []
    for key,val in dict.items(L):
        status_value.append(val[2])
    if status_value :
        if ( 1 in status_value ) or ( 3 in status_value) :
             exit (1)
        else:
             exit(0)
    else :
          exit(1)

