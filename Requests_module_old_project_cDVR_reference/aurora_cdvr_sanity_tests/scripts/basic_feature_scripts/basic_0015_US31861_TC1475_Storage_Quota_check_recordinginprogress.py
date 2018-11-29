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
from genChannelLineup import *
from readYamlConfig import readYAMLConfigs
from getCatalogServices import getCdvrServiceIds
from getOffers import getCdvrSubscriptionOffers
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite

###############################################################################################################################################
# TestSteps: Storage Quota checking at Schedule time with one active recording in progress and active recording has earlier end broadcast time
# STEP1:Ingest 3 events,which are of n,n+1,n+1 minutes duration .
# STEP2:Get the three event from the grid response ,the Add event 1 and event 2 and increase 2% of the duration. 
# STEP3:Modify the diskquota to the 2% of the  calculated duration 
# STEP4:Do Event 1 booking and verify booking Successfull.If it is successfull then wait to compleete the recording
# STEP5:Do the second booking and wait for state change to Recording
# STEP6:Do the third booking and wait for second recording to complete
# STEP7:Verify that due to Insufficient diskquota third booking fails
###############################################################################################################################################

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
           else:
                return 0
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
                 "TC1475":["US31861",message,status]
                }
 
    print "\n US31861: As a SP, when the system performs storage quota checking at scheduling the algorithm will include Recording in Progress  and Recorded events only"
    print "\n TC1475: Storage Quota checking at Schedule time with one active recording in progress and active recording has earlier end broadcast time"

    try:
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        #Initialize the variables
        timeout = 2
        remaining_diskquota = None
        bookedeventresponse = None
        old_diskquota = None
        full_diskquota1 = None
        grid_response2 = None
        grid_response1 = None
        serviceidlist =[]
        recordedcheckcounter = 0
        recordingcheckcounter = 0

        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        port_pps = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        upm_hosts = [cfg['upm']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']
        prefix = cfg['basic_feature']['household_prefix']
        ci_host =cfg['ci']['host']
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
        diskquota_headers_hh = {
            'Content-Type': 'text/plain',
            'Source-Type': 'WEB',
            'Source-ID': '211.209.128.25',
            }
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        printLog("Final list :"+ str(hosts_list),printflg)
        eventtitle = "recprodis" + str(random.randint(400,499))

        #Ingest the catalog to the CI Host
        print "### STEP1:Ingest 3 events,which are of n,n+1,n+1 minutes duration .####################################### \n\n"
        channel = ChannelLineup(BoundaryInMinutes=0)
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        timeslotinminutes1 = timeslotinminutes + 1
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=1,programIDPrefix = eventtitle)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes1,timeSlotCount=1,programIDPrefix = eventtitle)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes1,timeSlotCount=1,programIDPrefix = eventtitle)
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
        tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
        return tims_dict
    print "### STEP2:Get the three event from the grid response ,the Add event 1 and event 2 and increase 2% of the duration.############################################# \n\n"
    for (cmdc_host,pps_host,upm_host) in hosts_list :
        try :
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
            old_diskquota = fetch_full_details_diskquota(protocol,upm_host,port_upm,householdid,timeout,printflg=False)
            if old_diskquota:
                print  "Original Diskquota is "  + old_diskquota.content
                grid_response = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
                if grid_response:
                    contentId_dict = get_contentIddict_bytitle(grid_response,eventtitle)
                    print "ContentId dictionary from the grid response\n" + str(contentId_dict)
                    if contentId_dict:
                        random_contentIdlist = get_contentIdlist_allcontentiddict_channellineup(contentId_dict,printflg)
                        print "ContentId list after sorting\n" + str(random_contentIdlist)
                        if random_contentIdlist:
                            iterindex = 0
                            random_contentId = []
                            diskquota = []
                            prevdiskquota = 0
                            for items in random_contentIdlist:
                                if (iterindex < 3) and (items[3] >= prevdiskquota):
                                    randomcontentId = items[0]
                                    prevdiskquota = items[3]
                                    random_contentId.append(randomcontentId)
                                    diskquota.append(prevdiskquota)
                                    iterindex += 1
                            if (len(random_contentId) == 3) and (len(diskquota) == 3):
                                print "ContentId for the first booking " + random_contentId[0]
                                print "ContentId for the second booking " + random_contentId[1]
                                print "ContentId for the third booking " + random_contentId[2]
                                print "Duration of first booking " + str(diskquota[0])
                                print "Duration of second booking " + str(diskquota[1])
                                print "Duration of third booking " + str(diskquota[2])
                            
                                payload =  """{
                                    "checkConflicts": true,
                                    "pvr": "nPVR",
                                    "scheduleInstanceId": "%s"
                                    }"""%(random_contentId[0])
                                diskquota1 = int(diskquota[0])/1000 
                                diskquota2 = int(diskquota[1])/1000
                                diskquota3 =(diskquota1+diskquota2)
                                diskquota_mod=change_diskQuota_value("inc",diskquota3,"2")
                                diskquota=str(diskquota_mod)
                                print "### STEP3:Modify the diskquota to the 2% of the  calculated duration############################# \n\n"
                                modify_diskQuota(cfg,protocol,upm_host,port_upm,householdid,diskquota,diskquota_headers_hh,timeout,printflg=False)
                                full_diskquota = fetch_full_details_diskquota(protocol,upm_host,port_upm,householdid,timeout,printflg=False)
                                if full_diskquota:
                                    full_diskquota_old = full_diskquota.content
                                    printLog( "full diskquota is "  + full_diskquota.content,printflg)
                                    print "### STEP4:Do Event 1 booking and verify booking Successfull.If it is successfull then wait to compleete the recording######################################### \n\n"
                                    result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload,random_contentId[0],timeout,printflg=False)
                                    if result == "FAIL":
                                        message =  "Testcase Failed: PPS Booking failed for the event contentId %s" %(random_contentId[0])
                                        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                        print message
                                        tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                                        return tims_dict
                                    else:
                                        print "PPS booking is successful for the event contentId %s" %(random_contentId[0])
                                        time.sleep(fetch_bookingcatalog_delay)
                                        bookedeventresponse = fetch_bookingCatalog(port_pps,protocol,pps_host,householdid,timeout)
                                else:
                                    message =  "Testcase Failed: Unable to Fetch the Diskquota for the household after modifying the Diskquota"
                                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                    print message 
                                    tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                                    return tims_dict
                            else:
                                message =  "Testcase Failed: Length of contentIds and the diskquota is not as expected"
                                print message 
                                tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                                return tims_dict
                        else:
                             message =  "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                             print message 
                             tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                             return tims_dict
                    else:
                        mesage =  "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                        print message 
                        tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                        return tims_dict
                else:
                    message =  "Testcase Failed: Unable to Fetch Grid Response"
                    print message 
                    tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                    return tims_dict
            else:
                message =  "Testcase Failed: Unable to Fetch the Diskquota for the household"
                print message 
                tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                return tims_dict
            
            #Verify the first booking and wait till it completes the recording
            if bookedeventresponse:
                bookedeventcontent = json.loads(bookedeventresponse.content)
                for val in bookedeventcontent:
                    if val["scheduleInstance"] == random_contentId[0]:
                        printLog("Progam status for householdId " + householdid +" & " + random_contentId[0] ,printflg)
                        printLog("Program title" + val["title"] + "\nProgram state " + val["state"] +"\nProgram recordingId " + val["recordingId"] +"\nProgram Recording type " + val["type"] + "\nProgram Recurrence is " + val["recurrence"] + "\nProgram startTime is " + val["startTime"] + "\nProgram duration is " + val["duration"], printflg)
                        pgm_end_time = val['content']['endAvailability']
                        pgm_start_time = val['content']['broadcastDateTime']
                        pgm_start_wait_time= get_timedifference(pgm_start_time,printflg)
                        print "Program starts in " + str(pgm_start_wait_time/60) + " minutes"
                        time.sleep(pgm_start_wait_time)
                        time.sleep(recordingstatecheck_waittime)
                        recordingcatalogresult,recordingcontentresponse = verify_recording_state(port_pps,protocol,pps_host,householdid,random_contentId[0],timeout)
                        if recordingcatalogresult == "PASS" and recordingcontentresponse:
                            program_endtime = get_timedifference(pgm_end_time,printflg)
                            print "Program Recording completes in "+str(program_endtime/60)+" minutes"
                            print "Script will add " + str(recordedstatecheck_waittime/60) + " minute to program end time to check the Recorded State"
                            time.sleep(program_endtime)
                            time.sleep(recordedstatecheck_waittime)
                            recordedcatalogresult,recordedcontentresponse =verify_recorded_state(port_pps,protocol,pps_host,householdid,random_contentId[0],timeout)
                            if recordedcatalogresult == "PASS" and recordedcontentresponse:
                                full_diskquota1 = fetch_full_details_diskquota(protocol,upm_host,port_upm,householdid,timeout,printflg)
                                recordedcheckcounter += 1
                            else:
                                message =  "Testcase Failed: Unable to Verify Recorded Catalog"
                                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                print message 
                                tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                                return tims_dict
                        else:
                            message =  "Testcase Failed: Unable to Verify Recording Catalog"
                            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                            print message 
                            tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                            return tims_dict
            else:
                message =  "Testcase Failed: Unable to fetch Booked Catalog"
                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message 
                tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                return tims_dict
            print "### STEP5:Do the second booking and wait for state change to Recording###################### \n\n"
            #Do the second booking and wait for it to change to Recording
            if full_diskquota1 and recordedcheckcounter: 
                print  "Full diskquota after the recording completes is "  + full_diskquota1.content
                payload1 =  """{
                    "checkConflicts": true,
                    "pvr": "nPVR",
                    "scheduleInstanceId": "%s"
                    }"""%(random_contentId[1])
                result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload1,random_contentId[1],timeout,printflg)
                time.sleep(fetch_bookingcatalog_delay)
                if result == "FAIL":
                    message =  "Testcase Failed: PPS Booking failed for the event contentId %s" %(random_contentId[1])
                    debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message 
                    tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                    return tims_dict
                else:
                    print "PPS booking is successful for the event contentId %s" %(random_contentId[1])
                    event_state = fetch_bookingCatalog(port_pps,protocol,pps_host,householdid,timeout)
                    if event_state:
                       event_state = json.loads(event_state.content)
                       for val in event_state:
                           if val["scheduleInstance"] == random_contentId[1]:
                               if (val["state"] == "BOOKED" or val["state"] == "RECORDING"):
                                   printLog("Program status for householdId " + householdid +" & " + random_contentId[1] ,printflg)
                                   printLog("Program title" + val["title"] + "\nProgram state " + val["state"] +"\nProgram recordingId " + val["recordingId"] +"\nProgram Recording type " + val["type"] + "\nProgram Recurrence is " + val["recurrence"] + "\nProgram startTime is " + val["startTime"] + "\nProgram duration is " + val["duration"], printflg)
                                   pgm_end_time = val['content']['endAvailability']
                                   pgm_start_time = val['content']["broadcastDateTime"]
                                   pgm_start_wait_time = get_timedifference(pgm_start_time,printflg)
                                   time.sleep(pgm_start_wait_time)
                                   time.sleep(recordingstatecheck_waittime)
                                   recordingcatalogresult,recordingcontentresponse = verify_recording_state(port_pps,protocol,pps_host,householdid,random_contentId[1],timeout)
                                   if recordingcatalogresult and recordingcontentresponse:
                                       left_diskquota = fetch_diskspace_left(protocol,pps_host,port_pps,householdid,timeout,printflg)
                                       remaining_diskquota=bookedpgm_storage(left_diskquota)
                                       print "Remaining diskquota before scheduled booking is" + str(remaining_diskquota)
                                       recordingcheckcounter += 1
                                   else:
                                       message =  "Testcase Failed: Unable to Verify Recording Catalog"
                                       debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                       cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                       print message 
                                       tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                                       return tims_dict
                               else:
                                   message = "Testcase Failed: contentId is not in Booked Catalog"
                                   debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                   cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                   print message 
                                   tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                                   return tims_dict
                    else:
                        message = "Testcase Failed: Unable to fetch Booked Catalog"
                        debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                        print message 
                        tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                        return tims_dict
            else:
                message =  "Testcase Failed: Unable to Fetch the Diskquota for the household"
                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message 
                tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                return tims_dict
            #Do the third booking and wait for second recording to complete
            print "### STEP6:Do the third booking and wait for second recording to complete####################################################### \n\n"
            if remaining_diskquota and recordingcheckcounter:
                payload =  """{
                    "checkConflicts": true,
                    "pvr": "nPVR",
                    "scheduleInstanceId": "%s"
                    }"""%(random_contentId[2])
                result,response = do_PPSbooking_returnresponse(port_pps,protocol,pps_host,householdid,pps_headers,payload,random_contentId[2],timeout,printflg=False)
                print "### STEP7:Verify that due to Insufficient diskquota third booking fails########################################### \n\n"
                if result == "FAIL":
                    responsecontent = json.loads(response.content)
                    if (response.status_code == 403) and (responsecontent["message"] == "Disk Space Conflict Detected"):
                        print "PPS Booking failed for the event contentId %s" %(random_contentId[2])
                        message = "Testcase Passed: Insufficient diskquota third booking failed when the recording is in progress"
                        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,0,message,["TC1475"])
                        return tims_dict
                    else:
                        print "PPS Booking failed for the event contentId %s" %(random_contentId[2])
                        message = "Testcase Failed: PPS Booking failed due to unexpected reason"
                        debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                        return tims_dict
                else:
                    print "PPS booking is successful for the event contentId %s" %(random_contentId[2])
                    message = "Testcase Failed: Able to do the PPS Booking without any disk conflict"
                    debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                    return tims_dict
            else:
                message =  "Testcase Failed: Unable to Fetch the Diskquota for the household"
                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message 
                tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
                return tims_dict
        except :
            message = "Testcase Failed: Error Occured in Script " + PrintException(True)
            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC1475"])
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




