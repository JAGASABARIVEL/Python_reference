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
from os.path import isfile
import mypaths
import random
from readYamlConfig import readYAMLConfigs
from getCatalogServices import getCdvrServiceIds
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
from genChannelLineup import *

#####################################################################################################################################################################################################
# Test Steps: Schedule the Recording
# STEP1: Ingest 2 events(eg:Event1 and Event2) on one generic channel and 1 series of 2 episodes(Episode1 and Episode2) on another generic channel. 
# STEP2: Do the PPS Booking on 2 events,than 1 series booking sequentially. Store all 4 contentIds(Event1, Event2, Episode1, Episode2) in a list
# STEP3: Wait till the booking catalog fetch delay of both the events and series value taken from the config before fetching the booking catalog
# STEP4: Verify the Booked catalog has all 4 contentIds from the Step2 and than proceed further
# STEP5: Wait till the first program(Event1) broadcasttime and also give some time for the state change from the 'Booked' to 'Recording'
# STEP6: Verify the first program(Event1) is in Recording State and than proceed further(which means Episode1 should be in Recording state)
# STEP7: Wait till the last program(Event2) endAvailability time and than give some time for the state change from the 'Recording' to 'Recorded'
# STEP8: Verify all the contentIds are in the Recorded State, If the 'Recordedcounter=4' than proceed further, and pick the Event1 for the Playback
# STEP9: Playback the Recorded Event and Verify, cleanup the Event and update the Results
#####################################################################################################################################################################################################

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
            name  = os.path.basename(__file__)[:-3] 
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
            else:
                 return(0)
        else :
              print "status_value not present "
              return 1
    except:
          print  "Error Occurred in Script \n"
          PrintException()
          return (1)

def doit_wrapper(cfg,printflg=False):
    
    message = ""
    status = 3
    tims_dict = {
                 "TC910":["US31739",message,status],
                 "TC893":["US31833",message,status],
                 "TC895":["US31833",message,status]
                }
    
    print "US31739: UseCase: Schedule Event based Recording on Control Plane"
    print "TC910: Schedule Event based Recording"
    print "US31833: As a user I want to be able to setup playback session for recorded content"
    print "TC893: Playback from My Library"
    print "TC895: Playback till Endof File"

    try:
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        #Initialize the Variables
        timeout = 2
        serviceIdlist = []
        contentId = None
        recordedtitle = None
        contentplayuri = None
        catalogresponse = None
        statinfo = None
        bookedcatalogcounter = 0

        # set values based on config
        households_needed = cfg['basic_feature']['households_needed']
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceIdlist.append(unicode(testchannel1))
        testchannel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        serviceIdlist.append(unicode(testchannel2))
        prefix = cfg['basic_feature']['household_prefix']
        throttle_milliseconds = cfg['basic_feature']['throttle_milliseconds']
        prmsupportedflag = cfg['prm_supported']
        proxyhostcheckflag = cfg['proxyHostNeeded']
        proxy_host = cfg['proxyhost']['host']
        proxy_port = cfg['proxyhost']['port']
        contentplayback_host = cfg['contentplayback']['host']
        contentplayback_port = cfg['contentplayback']['port']
        contentplayback_url = cfg['contentplayback']['url']
        rm_host = cfg['rm']['host']
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        fetch_seriesbookingcatalog_delay = cfg['pps']['series_bookingstatecheck_waittime']
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
        hostlist = list(itertools.product(cmdc_hosts,pps_hosts))
        result = "Fail"
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        eventtitle1 = "recplay" + str(random.randint(1,999))
        eventtitle2 = "recplays" + str(random.randint(1,999))

        #Ingest the catalog to the CI Host
        print "### STEP1. Ingest 2 events(eg:Event1 and Event2) on one generic channel and 1 series of 2 episodes(Episode1 and Episode2) on another generic channel.###################### \n \n " 
        channel = ChannelLineup(BoundaryInMinutes=0)
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        channel.add_to_lineup(serviceId=testchannel2,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=2,programIDPrefix = eventtitle1)
        channel.add_to_lineup(serviceId=testchannel1,timeSlotLengthMinutes=timeslotinminutes,showID=eventtitle2,startEpisodeNumber=1,episodeCount=2,timeSlotCount=2)
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
    except:
        message = "Testcase Failed: Error Occured in configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
        return tims_dict

    #Do PPS Booking for the Events and the Series
    for (cmdc_host,pps_host) in hostlist :
        try:
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            #Get the Dictionary of ContentId and the values for PPS Booking
            print "### STEP2: Do the PPS Booking on 2 events,than 1 series booking sequentially. Store all 4 contentIds(Event1, Event2, Episode1, Episode2) in a list #################### \n \n "  
            gridservicelistresponse = fetch_gridRequest(catalogueId,protocol,cmdc_host,cmdc_port,serviceIdlist,region,timeout,printflg)
            if gridservicelistresponse:
                contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse,eventtitle1)
                seriescontentId_dict = get_series_contentIddict_bytitle(gridservicelistresponse,eventtitle2,['title','episodeNumber'])
                print "ContentId dictionary from the grid response\n" + str(contentId_dict_all) + str(seriescontentId_dict)
                if contentId_dict_all and seriescontentId_dict:
                    contentId_list = get_contentIdlist_allcontentiddict_channellineup(contentId_dict_all,printflg)
                    series_contentId_list = get_contentIdlist_allcontentiddict_channellineup(seriescontentId_dict,printflg)
                    print "ContentId list after sorting\n" + str(contentId_list) + str(series_contentId_list)
                    if (len(contentId_list)>1) and (len(series_contentId_list)>1):
                        contentId1 = contentId_list[0][0]
                        contentId2 = contentId_list[1][0]
                        series_contentId1 = series_contentId_list[0][0]
                        series_contentId2 = series_contentId_list[1][0]
                        broadcasttime_contentId1 = contentId_list[0][1]
                        endtime_contentId2 = contentId_list[1][2]
                        contentIdlist = [contentId1,contentId2]
                        print "Event ContentId list" +str(contentIdlist)
                        fullcontentIdlist = [contentId1,contentId2,series_contentId1,series_contentId2]
                        print "Event and Series ContentId list" + str(fullcontentIdlist)
                        for contentId in contentIdlist:
                            payload = """{
                                "scheduleInstanceId" : "%s",
                                "checkConflicts" : true,
                                "pvr":"nPVR"
                                }""" % (contentId)
                            result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,payload,contentId,timeout,printflg)
                            if result == "PASS":
                                print "PPS booking is successful for the event contentId %s" %contentId
                                bookedcatalogcounter += 1
                            else:
                                message = "Testcase Failed: PPS Booking failed for the event contentId %s" %contentId
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                                return tims_dict                            
                        series_payload = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true,
                            "pvr":"nPVR",
                            "recurrence":"SERIES"
                            }""" % (series_contentId1)
                        result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,series_payload,series_contentId1,timeout,printflg)
                        if result == "PASS":
                            print "PPS booking is successful for the series contentId %s" %series_contentId1
                            bookedcatalogcounter += 1
                        else:
                            message = "Testcase Failed: PPS Booking failed for the series contentId %s" %series_contentId1
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                            return tims_dict 
                    else:
                        message = "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Fetch Grid Response"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                return tims_dict

            #Getting Catalog Response for the Booked Catalog and wait till it starts recording and than wait till it completes the second program recording
            if bookedcatalogcounter > 2:
                print "### STEP3. Wait till the booking catalog fetch delay of both the events and series value taken from the config before fetching the booking catalog ################### \n \n "
                time.sleep(fetch_bookingcatalog_delay)
                time.sleep(fetch_seriesbookingcatalog_delay)
                print "###  STEP4. Verify the Booked catalog has all 4 contentIds from the Step2 and than proceed further ########################################### \n \n "
                bookedcatalogresult,catalogresponse = verify_booking(pps_port,protocol,pps_host,householdid,fullcontentIdlist,timeout)
                if bookedcatalogresult == "PASS" and catalogresponse:
                    print "### STEP5. Wait till the first program(Event1) broadcasttime and also give some time for the state change from the 'Booked' to 'Recording' ##################### \n \n " 
                    print "First Program starts broadcasting from " + str(broadcasttime_contentId1) + " (in epoch)"
                    wait_till_start_time = get_timedifference(broadcasttime_contentId1,printflg)
                    print "Script will wait for " + str(wait_till_start_time/60) + " minutes to start the recording by adding few minutes for the state change"
                    time.sleep(wait_till_start_time)
                    time.sleep(recordingstatecheck_waittime)
                    time.sleep(recordingstatecheck_waittime) #Additional delay for state change issue
                    time.sleep(recordingstatecheck_waittime) #Additional delay for state change issue
                    print "### STEP6. Verify the first program(Event1) is in Recording State and than proceed further(which means Episode1 should be in Recording state) ##################### \n \n"
                    recordingcatalogresult,recordingcatalogresponse = verify_recording_state(pps_port,protocol,pps_host,householdid,contentId1,timeout)
                    if recordingcatalogresult == "PASS" and recordingcatalogresponse:
                        print "First Program Recording Started and second Program completes at " + str(endtime_contentId2) + " (in epoch)"
                        wait_till_endtime = get_timedifference(endtime_contentId2,printflg)
                        print "Second Program Recording completes in "+str(wait_till_endtime/60)+" minutes"
                        print "Script will wait for" + str(wait_till_endtime/60) + " minutes to complete the recording by adding few minutes for the state change"
                        print "### STEP7. Wait till the last program(Event2) endAvailability time and than give some time for the state change from the 'Recording' to 'Recorded'# \n \n"
                        time.sleep(wait_till_endtime)
                        time.sleep(recordedstatecheck_waittime)
                        time.sleep(recordedstatecheck_waittime) #Additional delay for state change issue
                        time.sleep(recordedstatecheck_waittime) #Additional delay for state change issue
                    else:
                        message = "Testcase Failed: Unable to Verify Recording Catalog"
                        debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to Verify Booked Catalog"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                    return tims_dict
            else:
                message = "Testcase Failed: Count of Bookings is not as expected to proceed further"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                return tims_dict

            #Verify the Recorded Catalog and get the ContentPlayuri for Playback
            print "### STEP8. Verify all the contentIds are in the Recorded State,If the 'Recordedcounter=4 and proceed further, and pick the Event1 for the Playback  ############# \n \n "
            recordedcatalogresult,recordedcatalogresponse = verify_recorded_state(pps_port,protocol,pps_host,householdid,fullcontentIdlist,timeout)
            if recordedcatalogresult == "PASS" and recordedcatalogresponse:
                recordedcatalogcontent = json.loads(recordedcatalogresponse.content)
                for items in recordedcatalogcontent:
                    if items['scheduleInstance'] in fullcontentIdlist:
                        if items['state'] == "RECORDED":
                            recordedtitle = items['title']
                            contentplayuri = items['contentPlayUri']
                        else:
                            message = "Testcase Failed: contentId is not in Recorded Catalog"
                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                            return tims_dict
            else:
                message = "Testcase Failed: Unable to Verify Recorded Catalog"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
                return tims_dict
            print "### STEP9: Playback the Recorded Event and Verify, cleanup the Event and update the Results ######################################## \n \n "
            playback_recordedeventresult = "FAIL"
            playback_message = None
            playback_recordedeventresult,playback_message = playback_recordedevent(cfg,abspath,test,pps_headers,pps_port,pps_host,prmsupportedflag,proxyhostcheckflag,protocol,rm_host,contentplayback_host,contentplayback_port,proxy_host,proxy_port,contentplayback_url,contentplayuri,recordedtitle,householdid,timeout,printflg)
            if playback_recordedeventresult == "PASS" and playback_message:
                print playback_message
                tims_dict = update_tims_data(tims_dict,0,playback_message,["TC910","TC893","TC895"])
                return tims_dict
            else:
                print playback_message
                tims_dict = update_tims_data(tims_dict,1,playback_message,["TC910","TC893","TC895"])
                return tims_dict
        except:
            message = "Testcase Failed: Error Occured in Script " + PrintException(True)
            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC910","TC893","TC895"])
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

