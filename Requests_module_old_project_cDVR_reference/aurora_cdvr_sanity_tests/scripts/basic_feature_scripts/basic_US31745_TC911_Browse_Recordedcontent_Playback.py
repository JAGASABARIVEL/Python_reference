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

##############################################################################################################################################################################
# Testcase Steps: Browse the Recorded Event and playback the recorded video
# STEP1:  Ingest 2 events of n minutes each
# STEP2:  Fetch the grid request and get content id for booking & Do the PPS booking for the event
# STEP3:  Fetch booking catalog and verify the BOOKED state
# STEP4:  Fetch recording catalog, verify first event is in RECORDING state and wait till second event completes recording
# STEP5:  Verify RECORDED state from recorded catalog & Get 'content play uri' & 'recorded title' for playback
# STEP6:  Playback the Recorded Event and Verify, cleanup the Event and update the Results
###############################################################################################################################################################################

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
                "TC911":[ "US31745",message,status]
                }
    
    print "US31745: UseCase: Enable Subscriber Browse for Recorded Content via control plane"
    print "TC911: Enable Subscriber Browse for Recorded Content"

    try:
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
    
        #Initialize the Variables
        timeout = 2
        serviceIdlist = []
        random_contentId = None
        recordedtitle = None
        contentplayuri = None
        catalogresponse = None
        statinfo = None
        bookedcatalogcounter = 0
        recordingcatalogcounter = 0
        recordedcatalogcounter = 0
 
        # set values based on config
        households_needed = cfg['basic_feature']['households_needed']
        index = random.randint(0,households_needed-1)
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceIdlist.append(unicode(channel1))
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
        householdid = prefix + str(index)

        #Ingest the catalog to the CI Host
        print "###  STEP1: Ingest 2 events of n minutes each ##################################### \n \n "
        eventtitle = "brorecpla" + str(random.randint(500,599))
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=2,programIDPrefix = eventtitle)
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
        return tims_dict

    #Do PPS Booking
    for (cmdc_host,pps_host) in hostlist :
        try:
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            #Get the Dictionary of ContentId and the values for PPS Booking
            print "### STEP2: fetch the grid request and get content id for booking & Do the PPS booking for the event ##############\n \n" 
            gridservicelistresponse = fetch_gridRequest(catalogueId,protocol,cmdc_host,cmdc_port,serviceIdlist,region,timeout,printflg)
            if gridservicelistresponse:
                contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse,eventtitle,serviceparameterlist=[])
                print "ContentId dictionary from the grid response\n" + str(contentId_dict_all)               
                if contentId_dict_all:
                    contentId_list = get_contentIdlist_allcontentiddict_channellineup(contentId_dict_all,printflg)
                    print "ContentId list after sorting\n" +str(contentId_list)
                    if len(contentId_list)>1:
                        contentId1 = contentId_list[0][0]
                        contentId2 = contentId_list[1][0]
                        broadcasttime_contentId1 = contentId_list[0][1]
                        endtime_contentId2 = contentId_list[1][2]
                        contentIdlist = [contentId1,contentId2]
                        for contentId in contentIdlist:
                            payload = """{
                                "scheduleInstanceId" : "%s",
                                "checkConflicts" : true, 
                                "pvr":"nPVR"
                                }""" % (contentId)
                            result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,payload,contentId,timeout,printflg)
                            if result == "PASS":
                                print "PPS booking is successful for the event contentId %s"%contentId
                            else:
                                message = "Testcase Failed: PPS Booking failed for the event contentId %s" %(contentId)
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
                                return tims_dict
                    else:
                        message = "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Fetch Grid Response"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
                return tims_dict

            #Getting Catalog Response for the Booked Catalog and wait till it starts recording and than wait till it completes the second program recording
            print "### STEP3: Fetch booking catalog and verify the BOOKED state ###############################\n \n "
            time.sleep(fetch_bookingcatalog_delay)
            bookedcatalogresult,catalogresponse = verify_booking(pps_port,protocol,pps_host,householdid,contentIdlist,timeout)
            if bookedcatalogresult == "PASS" and catalogresponse: 
                wait_till_start_time = get_timedifference(broadcasttime_contentId1,printflg)
                print "### STEP4:  Fetch recording catalog, verify first event is in RECORDING state and wait till second event completes recording ###############"
                print "Program starts broadcasting from " + str(broadcasttime_contentId1) + " (in epoch)"
                print "Script will wait for " + str(wait_till_start_time/60) + " minutes to start the recording by adding few minutes for the state change"
                time.sleep(wait_till_start_time)
                time.sleep(recordingstatecheck_waittime)
                time.sleep(recordingstatecheck_waittime)#Additional delay for state change issue
                time.sleep(recordingstatecheck_waittime)#Additional delay for state change issue
                recordingcatalogresult,recordingcatalogresponse = verify_recording_state(pps_port,protocol,pps_host,householdid,contentId1,timeout)
                if recordingcatalogresult == "PASS" and recordingcatalogresponse:
                    print "First Program Recording Started and Second Program broadcasting completes at " + str(endtime_contentId2) + " (in epoch)"
                    wait_till_secondprogram_endtime = get_timedifference(endtime_contentId2,printflg)
                    print "Second Program Recording completes in "+str(wait_till_secondprogram_endtime/60)+" minutes"
                    print "Script will wait for" + str(wait_till_secondprogram_endtime/60) + " minutes to complete the recording by adding few minutes for the state change"
                    time.sleep(wait_till_secondprogram_endtime) 
                    time.sleep(recordedstatecheck_waittime)
                    time.sleep(recordedstatecheck_waittime)#Additional delay for the state change issue
                    time.sleep(recordedstatecheck_waittime)#Additional delay for the state change issue
                    recordingcatalogcounter += 1
                else:
                    message = "Testcase Failed: Unable to Verify Recording Catalog"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Verify Booked Catalog"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
                return tims_dict

            #Verify the Recorded Catalog and get the ContentPlayuri for Playback
            print "####### STEP5: Verify RECORDED state from recorded catalog & Get 'content play uri' & 'recorded title' for playback  #######\n \n"
            recordedcatalogresult,recordedcatalogresponse = verify_recorded_state(pps_port,protocol,pps_host,householdid,contentIdlist,timeout)
            if recordedcatalogresult == "PASS" and recordedcatalogresponse and recordingcatalogcounter:
                recordedcatalogcontent = json.loads(recordedcatalogresponse.content)
                for items in recordedcatalogcontent:
                    if items['scheduleInstance'] in contentIdlist:
                        if items['state'] == "RECORDED":
                            recordedtitle = items['title']
                            contentplayuri = items['contentPlayUri']
                            recordedcatalogcounter += 1
                        else:
                            message = "Testcase Failed: contentId is not in Recorded Catalog"
                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
                            return tims_dict
            else:
                message = "Testcase Failed: Unable to Verify Recorded Catalog"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
                return tims_dict                  
            #Playback of the recorded library
            print "### STEP6: Playback the Recorded Event and Verify, cleanup the Event and update the Results ######################################## \n \n "
            if recordedcatalogcounter == 2:
                playback_recordedeventresult = "FAIL"
                playback_message = None
                playback_recordedeventresult,playback_message = playback_recordedevent(cfg,abspath,test,pps_headers,pps_port,pps_host,prmsupportedflag,proxyhostcheckflag,protocol,rm_host,contentplayback_host,contentplayback_port,proxy_host,proxy_port,contentplayback_url,contentplayuri,recordedtitle,householdid,timeout,printflg)
                if playback_recordedeventresult == "PASS" and playback_message:
                    print playback_message
                    tims_dict = update_tims_data(tims_dict,0,playback_message,["TC911"])
                    return tims_dict
                else:
                    print playback_message
                    tims_dict = update_tims_data(tims_dict,1,playback_message,["TC911"])
                    return tims_dict
            else:
                message = "Testcase Failed: Recorded Events count is not enough to proceed further"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
                return tims_dict                  
        except:
            message = "Testcase Failed: Error Occurred in Script " + PrintException(True)
            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC911"])
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
        
