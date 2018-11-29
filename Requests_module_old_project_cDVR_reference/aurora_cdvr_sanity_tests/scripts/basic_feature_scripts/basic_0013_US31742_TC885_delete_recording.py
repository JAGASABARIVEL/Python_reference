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
from getCatalogServices import getCdvrServiceIds
from getOffers import getCdvrSubscriptionOffers
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from genChannelLineup import *
from jsonReadWrite import JsonReadWrite

#######################################################################################
# TC885: Record future program from EPG Grid, user delete recording from the recorded library
# STEP1: Ingest 2 events and 1 series of 2 episodes with n minutes each on 2 channels
# STEP2: Book the event and verify BOOKED state
# STEP3: Record the event and verify RECORDED state
# STEP4: Delete the event after recording, verify its not present in recording library
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
                "TC885":[ "US31742",message,status]
                }
    print tims_dict

    print "\nUS31742: UseCase: Delete single recording"
    print "\nTC885: Delete recording"

    try:
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
   
        #Initialize the variables
        timeout = 2
        serviceidlist =[]
        householdlimit = cfg['basic_feature']['households_needed']
        prefix = cfg['basic_feature']['household_prefix']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        gridservicelistresponse = None
        contentid_list = []
        startTime_list = []
        endTime_list = []
        contentURI = None 

        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        pps_port = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        channel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        serviceidlist.append(unicode(channel2))
        bookingCatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        booked_to_recording_delay = cfg['pps']['booked_to_recording_delay']
        recording_to_recorded_delay = cfg['pps']['recording_to_recorded_delay']
        upm_hosts = [cfg['upm']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
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
        title = 'deleterecev' + str(random.randint(1,100))
        householdid = prefix + str(index)
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        printLog("Host list :"+ str(hosts_list),printflg)
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        print "\n\n### STEP1: Ingest 2 events and 1 series of 2 episodes with n minutes each on 2 channels########################\n"
        timeslotinminutes = cfg['test_channels']['mediumProgramLength'] + roundofftonextint(booked_to_recording_delay)
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=2,programIDPrefix = title)
        channel.add_to_lineup(serviceId=channel2,timeSlotLengthMinutes=timeslotinminutes,showID=title,startEpisodeNumber=1,episodeCount=2,timeSlotCount=2)
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length =channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
    except:
        message = "Testcase Failed: Error Occured in configuration" + PrintException(True) 
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC885"])
        return tims_dict
    for (cmdc_host,pps_host,upm_host) in hosts_list :
      try:
        print "Cleaning up the household bookings and recordings before testcase execution"
        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
        print "\n\n### STEP2: Book the event and verify BOOKED state ######################################################################################################\n"
        gridservicelistresponse = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
        if gridservicelistresponse:
            contentid_dict = get_contentIddict_bytitle(gridservicelistresponse,title)
            print "ContentId dictionary from the grid response\n" + str(contentid_dict)
            if contentid_dict:
                contentid_sorted = sorted(contentid_dict.items(), key=lambda x:x[1])
            else:
                message = "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC885"])
                return tims_dict
            if len(contentid_sorted) > 2:
                print "ContentId list after sorting\n", contentid_sorted
            else:
                message = "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC885"])
                return tims_dict
            for items in contentid_sorted:
                contentid_list.append(items[0])
                startTime_list.append(items[1][0])
                endTime_list.append(items[1][1])
            print "List of all content ids for booking: ", contentid_list
            event_booking_result,event_booking_catalog = book_and_verify(pps_port,protocol,pps_host,householdid,pps_headers,contentid_list,bookingCatalog_delay,timeout)
            if event_booking_result == "PASS" and event_booking_catalog:
                print "\n\n### STEP3: Record the event and verify RECORDED state ########################################################################################\n"
                pgm_start_waitTime = get_timedifference(startTime_list[0],printflg)
                print "system will wait for ", pgm_start_waitTime, " seconds for program to start"
                time.sleep(pgm_start_waitTime)
                time.sleep(booked_to_recording_delay)
            else:
                message = event_booking_catalog
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,event_booking_catalog,["TC885"])
                return tims_dict 
            result_record, record_responce = record_and_verify(pps_port,protocol,pps_host,householdid,contentid_list,endTime_list,recording_to_recorded_delay,timeout,printflg)
            if result_record == "PASS" and record_responce:
                print"\n\n### STEP4: Delete the event after recording, verify its not present in recording library ############################################################\n"
                recordedresponsecontent = json.loads(record_responce.content)
                for val in recordedresponsecontent:
                    try:  
                        if val['scheduleInstance'] == contentid_list[0]:
                            contentURI = val['uri']
                    except:
                        pass
                if contentURI: 
                    delete_result = delete_PPSrecording(pps_port,protocol,pps_host,pps_headers,timeout,contentURI,printflg) 
                    if delete_result == "PASS":
                        verify_record_result, verify_record_responce = verify_recorded_state(pps_port,protocol,pps_host,householdid,contentid_list[0],timeout)
                        if verify_record_result == "FAIL":
                            message = "Testcase Passed: Event was succesfully deleted and verified from recorded library"
                            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,0,message,["TC885"])
                            return tims_dict
                        else:
                            message = "Testcase Failed: Unable to Verify Recorded Catalog"
                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC885"])
                            return tims_dict
                    else:
                        message = "Testcase Failed: Unable to Delete Recorded Event"
                        debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC885"])
                        return tims_dict   
                else: 
                    message = "Testcase Failed: Unable to fetch contentURI"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    print message    
                    tims_dict = update_tims_data(tims_dict,1,message,["TC885"])
                    return tims_dict
            else:
                message = record_responce
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC885"])
                return tims_dict 
        else:
            message = "Testcase Failed: Unable to Fetch Grid Response"
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC885"])
            return tims_dict
      except:
          message = "Testcase Failed: Error Occured in Script " + PrintException(True)
          debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
          cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
          print message
          tims_dict = update_tims_data(tims_dict,1,message,["TC885"])
          return tims_dict

# book_and_verify: This function does the booking for given payload, verifies the BOOKED state (calls L3 function 'verify_booking')
def book_and_verify(pps_port,protocol,pps_host,householdid,pps_headers,contentid_list,catalog_fetch_delay,timeout):
    try:
        bookedcounter = 0
        for contentid in contentid_list:
            payload = """{
                "scheduleInstanceId" : "%s",
                "checkConflicts" : true,
                "pvr":"nPVR"
                }""" % (contentid)
            result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,payload,contentid,timeout)
            if result == "PASS":
                print "PPS booking is successful for the event contentId %s" %contentid
                bookedcounter+=1
            else:
                message = "Testcase Failed: PPS Booking failed for the event contentId %s" %contentid
                return ("FAIL", message)
        if bookedcounter == len(contentid_list):
            time.sleep(catalog_fetch_delay)
            verify_book,responce = verify_booking(pps_port,protocol,pps_host,householdid,contentid_list,timeout)
            if verify_book == 'PASS':
                return ("PASS",responce)
            else:
                message = "Testcase Failed: Unable to Verify Booked Catalog"
                return ("FAIL", message)
        else:
            message = "Testcase Failed: PPS Booking failed for some events in the contentId list" +str(contentid_list)
            return ("FAIL",message)
    except:
        message = "Testcase Failed: Error Occured in Script "+ PrintException(True)
        return ("FAIL", message)

# record_and_verify : This function verifies RECORDING state (calls L3 'verify_recording_state'), waits for recording to complete, and verifies RECORDED state (calls L3 'verify_recorded_state')
def record_and_verify(pps_port,protocol,pps_host,householdid,content_id_list,endTime,recording_to_recorded_delay,timeout,printflg):
    try:
        recordingcatalogcounter = 0
        recordedcatalogcounter = 0
        result_recording, responce_recording = verify_recording_state(pps_port,protocol,pps_host,householdid,content_id_list[0],timeout)
        if result_recording == "PASS":
           recordingcatalogcounter += 1
           program_end_waittime = get_timedifference(endTime[-1],printflg)
           print "script will wait for " , str(program_end_waittime), " seconds for recording to complete"
           time.sleep(program_end_waittime)
        else:
           message =  "Testcase Failed: Unable to Verify Recording Catalog"
           return ("FAIL", message)
        if recordingcatalogcounter:
            time.sleep(recording_to_recorded_delay)
            result_recorded, responce_recorded = verify_recorded_state(pps_port,protocol,pps_host,householdid,content_id_list,timeout)
            if result_recorded == "PASS":
                return ("PASS", responce_recorded)
            else:
                message = "Testcase Failed: Unable to Verify Recorded Catalog"
                return ("FAIL", message)
        else:
           message =  "Testcase Failed: Unable to Verify Recording Catalog"
           return ("FAIL", message)
    except:
        message = "Testcase Failed: Error Occured in Script "+ PrintException(True)
        return ("FAIL", message)


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





