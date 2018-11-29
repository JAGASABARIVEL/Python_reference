#!/usr/bin/python

import os
import sys
import json
from pprint import pprint
import time
import requests
import calendar
import itertools
import mypaths
import random
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
from genChannelLineup import *

#######################################################################################
# TC871: Change Storage Quota from Billing System
#STEP1:Ingest the catalog for 4 individual event of n min each 
#STEP2:Fetch the content ID of all the three event and diskquota for all the three event 
#STEP3:Modify the diskquota as required by the first event booking , so that the storage quota is occupied  
#STEP4:Do the pps booking for the first event verify that the event is successfully recorded 
#STEP5:Modify the diskquota so that the storage quota is full and the second booking have unsufficient space 
#STEP6:Do pps booking for the second event , and verify that booking failed 
#STEP7:Modify the diskquota so that the storage quota have some empty space 
#STEP8:Do the pps booking for the third event, verify that the event is successfully recorded  
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
            else :
                return (0)
        else :
             print "status_value not present,Error in return code "
             return 1
    except:
          print  "Error Occurred in Script \n"
          PrintException()
          return (1)

def doit_wrapper(cfg,printflg=False):
    try :
        message = ""
        status = 3
        tims_dict = {
                 "TC871":["US31837",message,status]
                }
        print "\nUS31837:As a SP, I want a way to change the storage quota limit at the household level via my Billing System"
        print "\nTC871:Change Storage Quota from Billing System"

        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        #Initialize the Variables
        timeout = 2
        serviceIds =[]
        full_diskquota = None
        full_diskquota1 = None
        full_diskquota2 = None
        recordedcontentresponse = None
        recordedcatalogresult = None
        bookedcheckcounter = 0
        bookedcheckcounter1 = 0
        recordedcheckcounter = 0
        recordedcheckcounter1 = 0
    
        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        port_pps = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceIds.append(unicode(channel1))
        upm_hosts = [cfg['upm']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']
        fetch_bookingCatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        prefix = cfg['basic_feature']['household_prefix']

        print "### STEP1:Ingest the catalog for 4 individual event of n min each ###################################### \n \n "
        eventtitle = 'billchan' + str(random.randint(200,299))
        seconds = 1
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=4,programIDPrefix = eventtitle)
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
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
        diskquota_headers_hh = {
            'Content-Type': 'text/plain',
            'Source-Type': 'WEB',
            'Source-ID': '211.209.128.25',
            }
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
    except:
        message =  "Testcase Failed: Error Occured in configuration" + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
        return tims_dict

    for (cmdc_host,pps_host,upm_host) in hosts_list :
      try:
        print "Cleaning up the household bookings and recordings before testcase execution"
        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
        print "### STEP2:Fetch the content ID of all the three event and diskquota for all the three event ###################################### \n \n "
        old_diskquota = fetch_full_details_diskquota(protocol,upm_host,port_upm,householdid,timeout,printflg)
        if old_diskquota:
            print  "original  diskquota is "  + old_diskquota.content
            grid_response = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceIds,region,timeout,printflg)
            if grid_response:
                contentId_dict_all = get_contentIddict_bytitle(grid_response,eventtitle,['title'])
                print "ContentId dictionary from the grid response\n" + str(contentId_dict_all)
                if contentId_dict_all :
                    event_contentId_list = sorted(contentId_dict_all.items(), key=lambda x:x[1])
                    print "ContentId list after sorting\n" + str(event_contentId_list)
                    if len(event_contentId_list) >=2:
                        random_contentId = event_contentId_list[0][0]
                        random_contentId_1 = event_contentId_list[1][0]
                        random_contentId_2 = event_contentId_list[2][0]
                        diskquota = event_contentId_list[0][1][2]
                        diskquota_second_event = event_contentId_list[1][1][2]
                        diskquota_third_event = event_contentId_list[2][1][2]
                        payload1 =  """{
                            "checkConflicts": true,
                            "pvr": "nPVR",
                            "scheduleInstanceId": "%s"
                            }"""%(random_contentId)
                        print "### STEP3:Modify the diskquota as required by the first event booking , so that the storage quota is occupied ###################################### \n \n "
                        diskquota1 = diskquota/1000 + 60
                        diskquota =str(diskquota1)
                        if modify_diskQuota(cfg,protocol,upm_host,port_upm,householdid,diskquota,diskquota_headers_hh,timeout,printflg) == "PASS":
                            full_diskquota = fetch_full_details_diskquota(protocol,upm_host,port_upm,householdid,timeout,printflg)
                        else:
                            message = "Testcase Failed: Unable to Modify the Diskquota for the household"
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                            return tims_dict
                    else:
                        message =  "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                    return tims_dict
            else:
                message =  "Testcase Failed: Unable to Fetch Grid Response"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                return tims_dict
        else:
            message =  "Testcase Failed: Unable to Fetch the Diskquota for the household"
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
            return tims_dict
       
        #Do the First PPS Booking and Wait till state change to Recorded
        print "### STEP4:Do the pps booking for the first event verify that the event is successfully recorded ###################################### \n \n "
        if full_diskquota:
            print "full diskquota is "  + full_diskquota.content
            result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload1,random_contentId,timeout,printflg)
            if result == "PASS":
                print "PPS booking is successful for the event contentId %s" %(random_contentId)
                time.sleep(fetch_bookingCatalog_delay)
                event_state = fetch_bookingCatalog(port_pps,protocol,pps_host,householdid,timeout)
                if event_state:
                    event_state = json.loads(event_state.content)
                    for val in event_state:
                      if val["scheduleInstance"] == random_contentId:
                        if val["state"] == "BOOKED":
                            printLog("Progam status for householdId " + householdid +" & " + random_contentId ,printflg)
                            printLog("Program title" + val["title"] + "\nProgram state " + val["state"] +"\nProgram recordingId " + val["recordingId"] +"\nProgram Recording type " + val["type"] + "\nProgram Recurrence is " + val["recurrence"] + "\nProgram startTime is " + val["startTime"] + "\nProgram duration is " + val["duration"], printflg)
                            uri_delete = val['uri']
                            broadcaststarttime = val['content']['broadcastDateTime']
                            endavailabilitytime = val['content']['endAvailability']
                            print "Program starts broadcasting from " + str(broadcaststarttime) + " (in epoch)"
                            wait_till_start_time = abs(get_timedifference(broadcaststarttime,printflg))
                            print "Script will wait for " + str(wait_till_start_time/60) + " minutes to start the recording"
                            time.sleep(wait_till_start_time)
                            time.sleep(recordingstatecheck_waittime)
                            recordingresult, recordingresponse = verify_recording_state(port_pps,protocol,pps_host,householdid,random_contentId,timeout)
                            if recordingresult == "PASS" and recordingresponse:
                                print "Recording Started and Program broadcasting completes at " + str(endavailabilitytime) + " (in epoch)"
                                program_endtime = abs(get_timedifference(endavailabilitytime,printflg))
                                print "Program Recording completes in "+str(program_endtime/60)+" minutes"
                                check_after_end_time = endavailabilitytime + (recordedstatecheck_waittime*1000)
                                timedifference = abs(get_timedifference(check_after_end_time,printflg))
                                print "Script will add " + str(recordedstatecheck_waittime/60) + " minute to program end time and wait for "+str(int(timedifference/60))+" minutes to check the Recorded State"
                                time.sleep(timedifference)
                                recordedcatalogresult,recordedcontentresponse = verify_recorded_state(port_pps,protocol,pps_host,householdid,random_contentId,timeout)
                                bookedcheckcounter += 1
                            else:
                                message = "Testcase Failed: Unable to Verify Recording Catalog"
                                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                                return tims_dict
                        else:     
                            message =  "Testcase Failed: ContentId is not in the Booked Catalog"
                            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                            return tims_dict
                else:
                    message = "Testcase Failed: Unable to fetch Booked Catalog"
                    debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                    return tims_dict
            else:
                message =  "Testcase Failed: PPS Booking failed for the event contentId %s" %(random_contentId)
                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                return tims_dict
        else:
            message = "Testcase Failed: Unable to Fetch the Diskquota for the household"
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
            return tims_dict
 
        #Verify the Recording Catalog for the first Recorded Event and try again fetching diskspace 
        if recordedcontentresponse and recordedcatalogresult == "PASS":
            if random_contentId_1:
                print "Trying to attempt for second event booking"
                payload2 =  """{
                    "checkConflicts": true,
                    "pvr": "nPVR",
                    "scheduleInstanceId": "%s"
                    }"""%(random_contentId_1)
                print "### STEP5:Modify the diskquota so that the storage quota is full and the second booking have unsufficient space ################################# \n \n "
                diskquota2 = diskquota_second_event/1000 - 120
                diskquota =str(diskquota2)
                if modify_diskQuota(cfg,protocol,upm_host,port_upm,householdid,diskquota,diskquota_headers_hh,timeout,printflg=False)  == "PASS":
                    full_diskquota1 = fetch_full_details_diskquota(protocol,upm_host,port_upm,householdid,timeout,printflg=False) 
                    recordedcheckcounter += 1
                else:
                    message = "Testcase Failed: Unable to Modify the Diskquota for the household"
                    debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                    return tims_dict
            else:
                message =  "Testcase Failed: Unable to fetch contentId"
                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                return tims_dict
        else:
            message =  "Testcase Failed: Unable to Verify Recorded Catalog"
            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
            return tims_dict

        #Verify the second booking fails because of insufficient disk space than increase the total diskspace to accomodate the third booking
        print "### STEP6:Do pps booking for the second event , and verify that booking failed ###################################### \n \n "
        if full_diskquota1 and recordedcheckcounter:
            print "full diskquota is "  + full_diskquota1.content
            result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload2,random_contentId_1,timeout,printflg=False)
            if result == "FAIL":
                print "Second PPS Booking fails due to insufficient disk space for the event contentId %s" %(random_contentId_1)
                if random_contentId_2:
                    payload3 =  """{
                        "checkConflicts": true,
                        "pvr": "nPVR",
                        "scheduleInstanceId": "%s"
                        }"""%(random_contentId_2)
                    print "### STEP7.modify the diskquota so that the storage quota have some empty space ###################################### \n \n "
                    diskquota3 = diskquota_third_event/1000 + 120
                    diskquota3 = diskquota3 + diskquota1
                    diskquota =str(diskquota3)
                    if modify_diskQuota(cfg,protocol,upm_host,port_upm,householdid,diskquota,diskquota_headers_hh,timeout,printflg) == "PASS":
                        full_diskquota2 = fetch_full_details_diskquota(protocol,upm_host,port_upm,householdid,timeout,printflg)
                    else:
                        message = "Testcase Failed: Unable to Modify the Diskquota for the household"
                        debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                        return tims_dict
                else:
                    message =  "Testcase Failed: Unable to fetch contentId"
                    debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                    return tims_dict
            else:
                message =  "Testcase Failed: Able to do the PPS Booking without any disk conflict"
                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                return tims_dict
        else:
            message =  "Testcase Failed: Unable to Fetch the Diskquota for the household"
            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
            return tims_dict

        #Do the Third PPS Booking and verify that this should be successful because of sufficient disk space
        print "### STEP8:Do the pps booking for the third event, verify that the event is successfully recorded ###################################### \n \n "
        if full_diskquota2:
            print "Full diskquota of the household is "  + full_diskquota2.content
            result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload3,random_contentId_2,timeout,printflg=False)
            if result == "PASS":
                print "PPS booking is successful for the event contentId %s" %(random_contentId_2)
                time.sleep(fetch_bookingCatalog_delay)
                bookedcatalogresult1,bookedcatalogresponse1 = verify_booking(port_pps,protocol,pps_host,householdid,random_contentId_2,timeout)
                if bookedcatalogresult1 == "PASS" and bookedcatalogresponse1:
                    bookedcatalogcontent1 = json.loads(bookedcatalogresponse1.content)
                    for items1 in bookedcatalogcontent1:
                        if items1['scheduleInstance'] == random_contentId_2:
                            endavailability_contentid = items1['content']['endAvailability']
                            timedifference = get_timedifference(endavailability_contentid,printflg)
                            print "Script will wait for " + str(int(timedifference/60)) + " minutes by adding delay for the state change"
                            time.sleep(timedifference)
                            time.sleep(recordedstatecheck_waittime)
                            recordedcatalogresult1,recordedcatalogresponse1 = verify_recorded_state(port_pps,protocol,pps_host,householdid,[random_contentId,random_contentId_2],timeout)
                            if recordedcatalogresult1 == "PASS" and recordedcatalogresponse1:
                                recordedcheckcounter1 += 1
                    if recordedcheckcounter1:
                        message =  "Testcase Passed: Recording of last event is successful and no recordings is removed after increasing storage space"
                        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,0,message,["TC871"])
                        return tims_dict
                    else:
                        message =  "Testcase Failed: Recording is not successful or recordings is removed even after increasing storage space"
                        debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                        return tims_dict
                else:
                    message =  "Testcase Failed: Unable to Verify Booked Catalog"
                    debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                    return tims_dict
            else:
                message = "Testcase Failed: PPS Booking failed for the event contentId %s" %(random_contentId_2)
                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
                return tims_dict
        else:
            message =  "Testcase Failed: Unable to Fetch the Diskquota for the household"
            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
            return tims_dict
      except:
         message =  "Testcase Failed: Error Occured in Script " + PrintException(True)
         debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
         cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
         print message
         tims_dict = update_tims_data(tims_dict,1,message,["TC871"])
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



