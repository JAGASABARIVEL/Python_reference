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

#######################################################################################################
# TC873: Available storage quota displayed on UX
# STEP1: Ingest one event which is of n minute duration 
# STEP2: Fetch a random contentId from the grid response and perform event booking.
# STEP3: If booking is Successfull, fetch booking catalog and calculate the time to complete recording
# STEP4: Verify that the Booked Event is present in the record library 
# STEP5: Verify the available space after Recording completed
#######################################################################################################

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
            name  =   os.path.basename(__file__)[:-3]
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
                return 1
           elif (4 in status_value) or (2 in status_value):
                return (2)
           else:
                return 0
        else :
             print "status_value not present,Error in return code "
             return 1
    except:
          print  "Error Occurred in Script \n"
          PrintException()
          return (1)

def doit_wrapper(cfg,printflg=False):

    message = ""
    status = 3
    tims_dict = {
                 "TC873":["US31812",message,status]
                }

    print "\nUS31812: As a viewer, I want to be able to see my current storage quota status"
    print "\nTC873: Available storage quota displayed on UX"
 
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test

    try:    
        #Initialize the Variables
        timeout = 2
        recordedcheckcounter = 0
        serviceIdlist = []
        bookedcatalogresponse = None

        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        port_pps = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceIdlist.append(unicode(testchannel1))
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        prefix = cfg['basic_feature']['household_prefix']
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        upm_hosts = [cfg['upm']['host']]
        fetch_bookingCatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
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
        eventtitle = "avaispac" + str(random.randint(300,399))
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']

        #Ingest the catalog to the CI Host
        print "### STEP1:Ingest one event,which is of n minute duration .#######################################\n"
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=testchannel1,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=1,programIDPrefix = eventtitle)
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
        householdid = prefix + str(index)
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        printLog("Final list :"+ str(hosts_list),printflg)
    except:
        message = "Testcase Failed: Error Occured in configuration" + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
        return tims_dict

    print "### Step 2: Fetch a random contentId from the grid response and perform event booking.#################################################################\n"
    for (cmdc_host,pps_host,upm_host) in hosts_list :
        print "Cleaning up the household bookings and recordings before testcase execution"
        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
        try:
            grid_response = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceIdlist,region,timeout,printflg)
            if grid_response:
                 contentId_dict = get_contentIddict_bytitle(grid_response,eventtitle,['title'])
                 print "ContentId dictionary from the Grid Response\n" + str(contentId_dict)
                 if contentId_dict:
                     event_contentid_list = sorted(contentId_dict.items(), key=lambda x:x[1])
                     print "ContentId list after sorting\n" + str(event_contentid_list)
                     if len(event_contentid_list) > 0:
                         random_contentId = event_contentid_list[0][0]
                         payload =  """{
                             "checkConflicts": true,
                             "pvr": "nPVR",
                             "scheduleInstanceId": "%s"
                             }"""%(random_contentId)
                         full_diskquota = fetch_full_details_diskquota(protocol,upm_host,port_upm,householdid,timeout,printflg)
                         if full_diskquota:
                             print "Full Diskquota of the Household is "  + full_diskquota.content
                             full_diskquota =json.loads(full_diskquota.content)
                             left_diskquota = fetch_diskspace_left(protocol,pps_host,port_pps,householdid,timeout,printflg)
                             if left_diskquota:
                                 left_diskquota=bookedpgm_storage(left_diskquota)
                                 available_diskquota = left_diskquota
                                 print "Available diskquota is " + str(available_diskquota)
                                 result =do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload,random_contentId,timeout,printflg)
                                 if result == "PASS":
                                     print "PPS booking is successful for the event contentId %s" %random_contentId
                                     bookedcatalogresponse = fetch_bookingCatalog(port_pps,protocol,pps_host,householdid,timeout)
                                 else:
                                     message =  "Testcase Failed: PPS Booking failed for the event contentId %s" %(random_contentId)
                                     print message
                                     tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                                     return tims_dict
                             else:
                                 message =  "Testcase Failed: Unable to Fetch the Available Diskquota for the household"
                                 print message
                                 tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                                 return tims_dict
                         else:
                             message =  "Testcase Failed: Unable to Fetch the Diskquota for the household"
                             print message
                             tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                             return tims_dict
                     else:
                          message =  "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                          print message
                          tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                          return tims_dict
                 else:
                      message =  "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                      print message
                      tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                      return tims_dict
            else:
                message =  "Testcase Failed: Unable to Fetch Grid Response"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                return tims_dict

            #Verify the Recording Catalog for the Booked Event and verify the available space after Recording completed
            print "### STEP3: If booking is Successfull, fetch booking catalog and calculate the time to complete recording########################################################\n"
            if bookedcatalogresponse:
                json_contents =json.loads(bookedcatalogresponse.content)
                time.sleep(fetch_bookingcatalog_delay)
                for val in json_contents:
                    if val["scheduleInstance"] == random_contentId :
                        if val["state"] == "BOOKED":
                            uri_delete = val['uri']
                            pgm_end_time = val['content']['endAvailability']
                            pgm_start_time = val['content']["broadcastDateTime"]
                            pgm_start_wait_time= get_timedifference(pgm_start_time,printflg)
                            print "system wait time to start the program in Seconds " + str(pgm_start_wait_time)
                            time.sleep(pgm_start_wait_time)
                            time.sleep(recordingstatecheck_waittime)
                            time.sleep(recordingstatecheck_waittime)
                            recordingcatalogresult,recordingcontentresponse = verify_recording_state(port_pps,protocol,pps_host,householdid,random_contentId,timeout)
                            if recordingcatalogresult == "PASS" and recordingcontentresponse:
                                pgm_compleetetime = get_timedifference(pgm_end_time,printflg)
                                print "System  wait time  for compleete the recording after the start of the program  in Sec" + str( pgm_compleetetime)
                                time.sleep(pgm_compleetetime)
                                time.sleep(recordedstatecheck_waittime)
                                time.sleep(recordedstatecheck_waittime)#Additional delay for state change issue
                                print "### STEP4: Verify that the Booked Event is present in the record library####################################################\n"
                                recordedcatalogresult,recordedcontentresponse =verify_recorded_state(port_pps,protocol,pps_host,householdid,random_contentId,timeout)
                                if recordedcatalogresult == "PASS" and recordedcontentresponse:
                                    print "### STEP5: Verify the available space after Recording completed################################################\n"
                                    left_diskquota = fetch_diskspace_left(protocol,pps_host,port_pps,householdid,timeout,printflg)
                                    if left_diskquota:
                                        left_diskquota=bookedpgm_storage(left_diskquota)
                                        remaining_diskquota = left_diskquota
                                        print "Remaining diskquota after the first event recording is" + str(remaining_diskquota)
                                        if full_diskquota == remaining_diskquota:
                                            message =  "Testcase Failed: Available Diskquota is not changed after the recording gets completed"
                                            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                            print message
                                            tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                                            return tims_dict
                                        else:
                                            message =  "Testcase Passed: Available Diskquota is changed after the recording gets completed"
                                            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                            print message
                                            tims_dict = update_tims_data(tims_dict,0,message,["TC873"])
                                            return tims_dict
                                    else:
                                         message =  "Testcase Failed: Unable to Fetch the Diskquota for the household"
                                         debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                         cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                         print message
                                         tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                                         return tims_dict
                                else:
                                    message =  "Testcase Failed: Unable to Verify Recorded Catalog"
                                    debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                    print message
                                    tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                                    return tims_dict
                            else:
                                message = "Testcase Failed: Unable to Verify Recording Catalog"
                                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                                return tims_dict
                        else:
                            message =  "Testcase Failed: ContentId is not in the Booked Catalog"
                            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                            return tims_dict
            else:
                message = "Testcase Failed: Unable to fetch Booked Catalog"
                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
                return tims_dict
        except:
             message =  "Testcase Failed: Error Occured in Script " + PrintException(True)
             debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
             cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
             print message
             tims_dict = update_tims_data(tims_dict,1,message,["TC873"])
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


