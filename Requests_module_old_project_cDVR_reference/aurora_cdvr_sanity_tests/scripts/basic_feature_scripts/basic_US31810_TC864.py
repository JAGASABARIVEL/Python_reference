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

#########################################################################################################################################################################
# TC864: Tuner Quota Check at Series Booking creation - First Episode Only

# STEP1: Ingest Series1 and Series2 of 2 Episodes on 2 channels(n minutes) with the posttime of n minutes and another series of 1 episode into 3rd channel with the posttime of 2n minutes
# STEP2: Set the Tuner Quota to 2
# STEP3: Do the PPS Booking for 1st and 2nd Series and verify if both are successful
# STEP4: Do the PPS Booking for 3rd Series and verify it fails due to ""Tuner Conflict"" 
# STEP5: Revert back the original conditions, than update the results
#########################################################################################################################################################################
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
        if status_value:
           if ( 1 in status_value ) or ( 3 in status_value) :
                return 1
           else:
                return 0
        else:
             print "status_value not present,Error in return code "
             return 1
    except:
          print  "Error Occurred in script \n"
          PrintException()
          return (1)

def doit_wrapper(cfg,printflg=False):
    try :
       message = ""
       status = 3
       tims_dict = {
                 "TC864":["US31840",message,status],
                }
       print "\nUS31810: As a SP, when a series recording is created I want the cDVR System to perform Recording Tuner Quota checking on the first episode in the series"
       print "\nTC864: Tuner Quota Check at Series Booking creation - First Episode Only"
 
       #  announce
       abspath = os.path.abspath(__file__)
       scriptName = os.path.basename(__file__)
       (test, ext) = os.path.splitext(scriptName)
       print "Starting test " + test
       tims_log = []
       #Initialize the Variables
       serviceidlist =[]
       timeout = 2
       grid_response = None
       # set values based on config
       protocol = cfg['protocol']
       upm_port = cfg['upm']['port']
       port_pps = cfg['pps']['port']
       port_cmdc = cfg['cmdc']['port']
       region = cfg['region']
       catalogueId = cfg['catalogueId']
       channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
       serviceidlist.append(unicode(channel1))
       channel2 = cfg['test_channels']['GenericCh2']['ServiceId']
       serviceidlist.append(unicode(channel2))
       channel3 = cfg['test_channels']['GenericCh3']['ServiceId']
       serviceidlist.append(unicode(channel3))
       upm_hosts =  [cfg['upm']['host']]
       prefix = cfg['basic_feature']['household_prefix']
       pps_headers = {
                 'Content-Type': 'application/json',
                 'Source-Type': 'WEB',
                 'Source-ID': '127.0.0.1',
                 }
       upm_headers = {
                  'Content-Type':'text/plain',
                  'Source-Type':'WEB',
                  'Source-ID':'127.0.0.1',
                   'Accept': 'text/plain',
                 }
       upm_headers1 = {
                   'Content-Type':'text/plain',
                   'Source-Type':'WEB',
                   'Source-ID':'211.209.128.25',
                }
       pps_hosts = [cfg['pps']['host']]
       cmdc_hosts = [cfg['cmdc']['host']]
       hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
       printLog("Final list :"+ str(hosts_list),printflg)
       householdlimit = cfg['basic_feature']['households_needed']
       index = random.randint(0,householdlimit-1)
       householdid = prefix + str(index)
       print "\n\n### STEP1: Ingest Series1 and Series2 of 2 Episodes on 2 channels(n minutes) with the posttime of n minutes and another series of 1 episode into 3rd channel with the posttime of 2n minutes #######################\n"
       ci_host =cfg['ci']['host']
       ci_port = cfg['ci']['port']
       booked_to_recording_delay = cfg['pps']['booked_to_recording_delay']
       fiveminuteprogramlength = cfg['test_channels']['longProgramLength'] + roundofftonextint(booked_to_recording_delay)
       eventprogramlength = fiveminuteprogramlength * 2
       title_1 = 'sertunco1' + str(random.randint(1,99))
       title_2 = 'sertunco2' + str(random.randint(100,199))
       title_3 = 'sertunco3' + str(random.randint(200,299))
       title_list = [title_1,title_2]
       ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
       ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
       seconds = 1
       post_time = time.time() + (seconds * fiveminuteprogramlength * 60) + ingest_minimum_delay
       post_time2 = time.time() + (seconds * fiveminuteprogramlength * 120) + ingest_minimum_delay
       channel = ChannelLineup(BoundaryInMinutes=0)
       channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=fiveminuteprogramlength,showID=title_1,episodeCount=2,startEpisodeNumber=1,timeSlotCount=2)
       channel.add_to_lineup(serviceId=channel2,timeSlotLengthMinutes=fiveminuteprogramlength,showID=title_2,episodeCount=2,startEpisodeNumber=1,timeSlotCount=2)
       post_time2 = channel.postXmlData(ci_host,ci_port,startTime = post_time)
       channel.writeXmlFiles(startTime = post_time)       
       print channel
       length1 = channel.getTotalLength()
       channel_2 = ChannelLineup(BoundaryInMinutes=0)
       channel_2.add_to_lineup(serviceId=channel3,timeSlotLengthMinutes=fiveminuteprogramlength,showID=title_3,episodeCount=1,startEpisodeNumber=1,timeSlotCount=1)
       channel_2.postXmlData(ci_host,ci_port,startTime = post_time2)
       channel_2.writeXmlFiles(startTime = post_time2)
       print channel_2
       length2 = channel_2.getTotalLength()
       length = length1 + length2 
       sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
       print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
       time.sleep(sleep_channel)
       booking_pass_counter = 0
    except:
        message =  "Testcase Failed: Error Occured in script: " + PrintException(True)
        print message 
        tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
        return tims_dict
    for (cmdc_host,pps_host,upm_host) in hosts_list :
        print "Cleaning up the household bookings and recordings before testcase execution"
        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
        try :
            print "\n\n### STEP2: Set the Tuner Quota to 2 #########################\n"
            print "Fetching Number of tuners in the Household"
            default_tunerquota = get_numberoftuners(protocol,upm_host,upm_port,upm_headers,householdid,timeout)
            if default_tunerquota:
                setTuner_result = set_numberoftuners(protocol,upm_host,upm_port,upm_headers1,householdid,timeout,"2")
                if setTuner_result == "PASS": 
                    updated_tunerquota = get_numberoftuners(protocol,upm_host,upm_port,upm_headers,householdid,timeout)
                    if updated_tunerquota:
                        if (updated_tunerquota == "2"):
                            grid_response = fetch_gridRequest_lessthancurrenttime(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
                            if grid_response:                                    
                                print "\n\n### STEP3: Do the PPS Booking for 1st and 2nd Series and verify if both are successful ###########################\n"
                                for title in title_list:
                                    contentId_dict = get_all_series_contentIddict_currentandfuture_bytitle(grid_response,title,['title','seriesId','episodeNumber'])
                                    if contentId_dict:
                                        series_contentId = sorted(contentId_dict.items(), key=lambda x:x[1])
                                        if series_contentId:
                                            content_id = series_contentId[0][0]
                                            payload = """
                                                      {
                                                       "scheduleInstanceId" : "%s",
                                                       "checkConflicts" : true,
                                                       "pvr":"nPVR",
                                                       "recurrence":"SERIES"
                                                      }
                                                       """ % (content_id)
                                            print "Content id to be booked: ", series_contentId
                                            result,response  = do_PPSbooking_returnresponse(port_pps,protocol,pps_host,householdid,pps_headers,payload,content_id,timeout,printflg=False)
                                            if result == "PASS" :
                                                print "PPS booking is successful for title: " , title
                                                booking_pass_counter = booking_pass_counter + 1
                                            else:
                                                responsecontent = json.loads(response.content)
                                                if (response.status_code == 403) and (responsecontent["message"] == "Tuner Conflict Detected"):
                                                    message =  "PPS Booking failed due to Tuner Conflict for title: " + title
                                                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                                    print message
                                                    tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                                                    return tims_dict
                                                else:
                                                    message = "PPS Booking failed for the series contentId %s" %(content_id) + "for title: " + title
                                                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                                    print message
                                                    tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                                                    return tims_dict
                                        else:
                                            message = "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                                            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                            print message
                                            tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                                            return tims_dict
                                    else:  
                                         message =  "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                                         debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                         cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                         print message
                                         tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                                         return tims_dict
                            else:
                                message = "Testcase Failed: Unable to Fetch Grid Response"
                                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                                return tims_dict
                        else:
                             message = "Testcase Failed: Unable to Modify the numberoftuners for the household,updated value different from the set value"
                             debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                             cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                             print message
                             tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                             return tims_dict
                    else:
                         message = "Testcase Failed: Unable to Fetch the updated numberoftuners for the household"
                         debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                         cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                         print message
                         tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                         return tims_dict
                else:
                     message = "Testcase Failed: Unable to Modify the numberoftuners for the household"
                     debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                     cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                     print message
                     tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                     return tims_dict
            else:
                 message = "Testcase Failed: Unable to Fetch the numberoftuners for the household"
                 debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                 cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                 print message
                 tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                 return tims_dict

            if (booking_pass_counter == len(title_list)) :
                 print "PPS booking succesful for first 2 events"
            else:
                 message = "Testcase Failed: Unable to book first 2 events"
                 debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                 cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                 print message
                 tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                 return tims_dict
            print "\n\n### STEP4: Do the PPS Booking for 3rd Series and verify it fails due to ""Tuner Conflict"" ###############\n"
            if grid_response:
                contentId_dict = get_all_series_contentIddict_currentandfuture_bytitle(grid_response, title_3, ['title', 'seriesId', 'episodeNumber'])
                if contentId_dict:
                    series_contentId = sorted(contentId_dict.items(), key=lambda x: x[1])
                    if series_contentId:
                        print "Content id list for title: ", title_3, "is: ", series_contentId
                        content_id = series_contentId[0][0]
                        payload = """
                                 {
                                 "scheduleInstanceId" : "%s",
                                 "checkConflicts" : true,
                                 "pvr":"nPVR",
                                 "recurrence":"SERIES"
                                 }
                                 """ % (content_id)
                        result, response = do_PPSbooking_returnresponse(port_pps, protocol, pps_host, householdid, pps_headers, payload, content_id, timeout, printflg=False)
                        if result == "PASS":
                            message = "Testcase Failedd: Able to do PPS Booking without tuner conflict"
                            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                            return tims_dict
                        else:
                            responsecontent = json.loads(response.content)
                            if (response.status_code == 403) and (responsecontent["message"] == "Tuner Conflict Detected"):
                                message = "Testcase Passed : PPS Booking failed due to Tuner Conflict"
                                print "\n\n### STEP5: Revert back the original conditions, than update the results ###########################\n"
                                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,0,message,["TC864"])
                                return tims_dict
                            else:
                                message = "Testcase Failed : PPS Booking Failed due to unexpected reason"
                                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                                return tims_dict
                    else:
                        message = "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                        debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                    return tims_dict
            else:
                 message = "Testcase Failed: Unable to Fetch Grid Response"
                 debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                 cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                 print message
                 tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
                 return tims_dict
        except :
             message =  "Testcase Failed: Error Occured in script: " + PrintException(True)
             debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
             cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
             print message 
             tims_dict = update_tims_data(tims_dict,1,message,["TC864"])
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


