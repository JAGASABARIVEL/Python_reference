#!/usr/bin/python
import os
import sys
import json
from pprint import pprint
import time
import requests
import calendar
import itertools
import random
import mypaths
from readYamlConfig import readYAMLConfigs
from getCatalogServices import getCdvrServiceIds
from getOffers import getCdvrSubscriptionOffers
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from os.path import isfile
import datetime
from genChannelLineup import *
from jsonReadWrite import JsonReadWrite

#############################################################################################################
# Teststeps: Activate RecordNow on a broadcast event from EPG
# STEP1:Ingest two events of x minutes duration.
# STEP2: Fetch currently broadcasting event from the grid response and perform booking.
# STEP3: Ftech the booked catalog and verify the state change happening from booked to recording.
# STEP4: Fetch the record library and calculate the time to compleete the recording and wait for compleete recording.
# STEP5: Fetch the recorded library and verify whether the booked event recorded successfully.
# STEP6:  Playback the Recorded Event and Verify, cleanup the Event and update the Results
#######################################################################################

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
          print  "Error Occurred in Script \n"
          PrintException()
          return (1)

def doit_wrapper(cfg,printflg=False):

    message = ""
    status = 3
    tims_dict = {
                "TC906":[ "US31797",message,status],
                "TC902":[ "US31798",message,status]
                }
    print "US31797: As a viewer, I want to select individual live shows from an EPG for immediate recording"
    print "TC906: (Copy of) Activate RecordNOW from EPG"
    print "US31798: As a viewer, I want to be able to press the RECORD button on my remote while watching live content and have the event recorded from that point to the end of the event"
    print "TC902: Activate RecordNOW on a broadcast event"
    try:
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
   
        #Initialize the variables
        timeout = 2
        serviceidlist =[]
        grid_response = None
        contentId_dict = None
        recordedcontentresponse = None
        recordingcatalogresponse = None
        recordedtitle = None
        contentplayuri = None
        statinfo = None
        contentplaybackstarttime = None
        contentplaybackendtime = None
        recordedcontentduration = None

        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        pps_port = cfg['pps']['port']
        cmdc_port = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        upm_hosts = [cfg['upm']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        prmsupportedflag = cfg['prm_supported']
        proxyhostcheckflag = cfg['proxyHostNeeded']
        proxy_host = cfg['proxyhost']['host']
        proxy_port = cfg['proxyhost']['port']
        contentplayback_host = cfg['contentplayback']['host']
        contentplayback_port = cfg['contentplayback']['port']
        contentplayback_url = cfg['contentplayback']['url']
        rm_host = cfg['rm']['host']
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
        post_time = time.time()
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        printLog("Final list :"+ str(hosts_list),printflg)
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        post_time = time.time() + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['longProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        eventtitle = "recdnwepg" + str(random.randint(700,799))
        #Ingest the Catalog to the CI Host
        print "### STEP1:Ingest two events of x minutes duration.################################################\n\n"
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=2,programIDPrefix = eventtitle)
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime=post_time)
        channel.writeXmlFiles(startTime=post_time)
        print channel
        length =channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
        return tims_dict
    print "### STEP2: Fetch currently broadcasting event from the grid response and perform booking.################################\n\n"
    for (cmdc_host,pps_host,upm_host) in hosts_list :
        try:
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            #Get the ContentId from the Grid which is broadcasting and do the PPS Booking
            grid_response = fetch_gridRequest_lessthancurrenttime(catalogueId,protocol,cmdc_host,cmdc_port,serviceidlist,region,timeout,printflg)
            if grid_response:
                contentId_dict = get_currentandfuture_contentIddict(grid_response,eventtitle,['title'])
                print "Programs from Grid Request which is currently broadcasting\n" + str(contentId_dict)
                if contentId_dict:
                    contentId_list = get_contentIdlist_allcontentiddict_channellineup(contentId_dict,printflg)
                    print "ContentId list after sorting\n" + str(contentId_list)
                    if len(contentId_list)>1:
                        current_broadcasting_contentId = contentId_list[0][0] 
                        current_broadcasting_starttime = contentId_list[0][1]
                        current_broadcasting_endtime = contentId_list[0][2]
                        payload =  """{
                            "checkConflicts": true,
                            "pvr": "nPVR",
                            "scheduleInstanceId": "%s"
                            }"""%(current_broadcasting_contentId)
                        result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,payload,current_broadcasting_contentId,timeout,printflg=False)
                        print "### STEP3: Fetch the booked catalog and verify the state change happening from booked to recording.######################################\n\n"
                        time.sleep(fetch_bookingcatalog_delay)
                        if result == "PASS":
                            print "PPS booking is successful for the event contentId %s" %(current_broadcasting_contentId)
                            bookingcatalogresult,bookingcatalogresponse = verify_booking(pps_port,protocol,pps_host,householdid,current_broadcasting_contentId,timeout)
                            if bookingcatalogresult == "PASS" and bookingcatalogresponse:
                                print "System will wait for " + str(recordingstatecheck_waittime/60) + " minutes for the state change from Booked to Recording"
                                time.sleep(recordingstatecheck_waittime)
                                time.sleep(recordingstatecheck_waittime) #Additional delay for state change issue
                                time.sleep(recordingstatecheck_waittime) #Additional delay for state change issue
                                print "### STEP4: Fetch the record library and calculate the time to compleete the recording and wait for compleete recording.##########################\n\n"
                                recordingcatalogresult,recordingcatalogresponse = verify_recording_state(pps_port,protocol,pps_host,householdid,current_broadcasting_contentId,timeout)
                            else:
                                message = "Testcase Failed: Unable to Verify Booked Catalog"
                                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
                                return tims_dict
                        else:
                            message = "Testcase Failed: PPS Booking failed for the event contentId %s" %(current_broadcasting_contentId)
                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
                            return tims_dict
                    else:
                        message = "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Fetch Grid Response"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
                return tims_dict
 
            #Verify the Recording Catalog for the Booked Event and verify after Recording completed
            if recordingcatalogresult == "PASS" and recordingcatalogresponse:
                recordingcatalogcontent = json.loads(recordingcatalogresponse.content)
                for val in recordingcatalogcontent:
                    if val["scheduleInstance"] == current_broadcasting_contentId:
                        if val["state"] == "RECORDING":
                            recordingstarttime = val["startTime"]
                            printLog("Progam status for householdId " + householdid +" & " + current_broadcasting_contentId ,printflg)
                            printLog("Program title" + val["title"] + "\nProgram state " + val["state"] +"\nProgram recordingId " + val["recordingId"] +"\nProgram Recording type " + val["type"] + "\nProgram Recurrence is " + val["recurrence"] + "\nProgram startTime is " + val["startTime"] + "\nProgram duration is " + val["duration"], printflg)
                            booking_recordingId = val['recordingId']
                            pgm_end_time = val['content']['endAvailability']
                            program_endtime = get_timedifference(pgm_end_time,printflg)
                            print "Program Recording completes in "+str(program_endtime/60)+" minutes"
                            time.sleep(program_endtime)
                            time.sleep(recordedstatecheck_waittime)
                            time.sleep(recordedstatecheck_waittime) #Additional delay for state change issue
                            print "### STEP5: Fetch the recorded library and verify whether the booked event recorded successfully.###################################\n\n"
                            recordedcatalogresult,recordedcontentresponse = verify_recorded_state(pps_port,protocol,pps_host,householdid,current_broadcasting_contentId,timeout)
                            if recordedcatalogresult == "PASS" and recordedcontentresponse:
                                jsonrecordedcontent = json.loads(recordedcontentresponse.content)
                                for rec_items in jsonrecordedcontent:
                                    if rec_items['scheduleInstance'] == current_broadcasting_contentId:
                                        if rec_items['state'] == "RECORDED":
                                            recordedtitle = rec_items['title']
                                            contentplayuri = rec_items['contentPlayUri'] 
                                            recordedcontentduration = rec_items['duration']
                                        else:
                                            message = "Testcase Failed: contentId is not in Recorded Catalog"
                                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                                            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                            print message
                                            tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
                                            return tims_dict
                            else:
                                message ="Testcase Failed: Unable to Verify Recorded Catalog"
                                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
                                return tims_dict
                        else:
                            message = "Testcase Failed: contentId is not in Recording Catalog"
                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
                            return tims_dict
            else:
                message = "Testcase Failed: Unable to Verify Recording Catalog"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
                return tims_dict
            print "### STEP6:  Playback the Recorded Event and Verify, cleanup the Event and update the Results ################### \n \n"
            playback_recordedeventresult = "FAIL"
            playback_message = None
            playback_recordedeventresult,playback_message = playback_recordedevent(cfg,abspath,test,pps_headers,pps_port,pps_host,prmsupportedflag,proxyhostcheckflag,protocol,rm_host,contentplayback_host,contentplayback_port,proxy_host,proxy_port,contentplayback_url,contentplayuri,recordedtitle,householdid,timeout,printflg)
            if playback_recordedeventresult == "PASS" and playback_message:
                print playback_message
                tims_dict = update_tims_data(tims_dict,0,playback_message,["TC906","TC902"])
                return tims_dict
            else:
                print playback_message
                tims_dict = update_tims_data(tims_dict,1,playback_message,["TC906","TC902"])
                return tims_dict
        except:
             message = "Testcase Failed: Error Occurred in Script" + PrintException(True)
             debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
             cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
             print message
             tims_dict = update_tims_data(tims_dict,1,message,["TC906","TC902"])
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
        if ( 1 in status_value ) or ( 3 in status_value) or ( 4 in status_value):
             exit (1)
        else:
             exit(0)
    else :
          exit(1)




