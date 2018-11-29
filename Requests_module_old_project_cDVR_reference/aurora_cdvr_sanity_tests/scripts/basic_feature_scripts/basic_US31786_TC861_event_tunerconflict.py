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
# Teststeps: Conflict, 1 tuner, 2 overlap current series
# STEP1: Ingest 2 events in 2 channels at the same time
# STEP2: Change the tuner quota to 1
# STEP3: Do 2 bookings,Second booking will fail
# STEP4: Change the tuner quota to 2 and then try the 2nd booking and see if it succeeds
# STEP5: Revert back to the original value which is stored initially from UPM
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
        if status_value :
           if ( 1 in status_value ) or ( 3 in status_value) :
                return 1
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
    try :
        message = ""
        status = 3
        tims_dict = {
                 "TC861":["US31786",message,status],
                }
        print "US31786: As a SP, I want an API to be able to change from my Billing System the recorder tuner quota for a household account"
        print "TC861:Change household Tuner Quota"
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
        tims_log = []
        #Initialize the Variables
        serviceidlist =[]
        timeout = 2
        grid_response = None
        random_contentId_list =[]
        booking_pass_counter = 0
        booking_fail_counter = 0
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
        upm_hosts =  [cfg['upm']['host']]
        prefix = cfg['basic_feature']['household_prefix']
        fetch_bookingCatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
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
        print "### STEP1: Ingest 2 events in 2 channels at the same time ##################################### \n\n"
        householdid = prefix + str(index)
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        eventtitle = 'tunconover' + str(random.randint(1,554))
        eventtitle1 = 'tunconover' + str(random.randint(555,999))
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength']
        eventtitle_list = [eventtitle,eventtitle1]
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=1, programIDPrefix=eventtitle)
        channel.add_to_lineup(serviceId=channel2,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=1, programIDPrefix=eventtitle1)
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
    except :
        message =  "Testcase failed : Error Occured in Script " + PrintException(True)
        print message 
        tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
        return tims_dict
    for (cmdc_host,pps_host,upm_host) in hosts_list :
        print "Cleaning up the household bookings and recordings before testcase execution"
        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
        try :
            print "### STEP2: Change the tuner quota to 1 ######################################################### \n\n"
            print "Fetching Number of tuners in the Household"
            default_tunerquota = get_numberoftuners(protocol,upm_host,upm_port,upm_headers,householdid,timeout)
            if default_tunerquota:
                setTuner_result = set_numberoftuners(protocol,upm_host,upm_port,upm_headers1,householdid,timeout,"1")
                if setTuner_result == "PASS": 
                    updated_tunerquota = get_numberoftuners(protocol,upm_host,upm_port,upm_headers,householdid,timeout)
                    if updated_tunerquota:
                        if (updated_tunerquota == "1"):
                            print "### STEP3: Do 2 bookings,Second booking will fail ######################################################### \n\n"
                            grid_response = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
                            if grid_response:
                                for eventtitle in eventtitle_list:
                                    contentId_dict = get_contentIddict_bytitle(grid_response,eventtitle,['title'])
                                    print "ContentId dictionary from the grid response\n" + str(contentId_dict)
                                    if contentId_dict:
                                        event_contentId_list = sorted(contentId_dict.items(), key=lambda x:x[1])
                                        print "ContentId list after sorting\n" + str(event_contentId_list)
                                        if event_contentId_list:
                                            random_contentId = event_contentId_list[0][0]
                                            random_contentId_list.append(random_contentId)
                                            payload =  """{
                                               "checkConflicts": true,
                                               "pvr": "nPVR",
                                               "scheduleInstanceId": "%s"
                                               }"""%(random_contentId)
                                            result,response  = do_PPSbooking_returnresponse(port_pps,protocol,pps_host,householdid,pps_headers,payload,random_contentId,timeout,printflg=False)
                                            if result == "PASS" :
                                                print "PPS booking is successful for the event contentId %s" %(random_contentId)
                                                booking_pass_counter = booking_pass_counter + 1
                                                time.sleep(fetch_bookingCatalog_delay)
                                            else:
                                                responsecontent = json.loads(response.content)
                                                if (response.status_code == 403) and (responsecontent["message"] == "Tuner Conflict Detected"):
                                                    print  "PPS Booking failed for the event contentId %s" %(random_contentId)
                                                    message =  "PPS Booking failed due to Tuner Conflict"
                                                    print message
                                                    booking_fail_counter = booking_fail_counter + 1
                                                else:
                                                    message =  "Testcase Failed: PPS Booking Failed due to unexpected reason"
                                                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                                    print message
                                                    tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                                                    return tims_dict
                                        else:
                                            message = "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                                            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                            print message
                                            tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                                            return tims_dict
                                    else:  
                                         message =  "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                                         cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                         print message
                                         tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                                         return tims_dict
                            else:
                                message = "Testcase Failed: Unable to Fetch Grid Response"
                                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                                return tims_dict
                        else:
                             message = "Testcase Failed: Count of Numberoftuners for the household is not as expected"
                             cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                             print message
                             tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                             return tims_dict
                    else:
                         message = "Testcase Failed: Unable to Fetch the numberoftuners for the household"
                         cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                         print message
                         tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                         return tims_dict
                else:
                     message = "Testcase Failed: Unable to Modify the numberoftuners for the household"
                     cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                     print message
                     tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                     return tims_dict
            else:
                 message = "Testcase Failed: Unable to Fetch the numberoftuners for the household"
                 cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                 print message
                 tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                 return tims_dict
            if ((booking_pass_counter == 1) and (booking_fail_counter == 1)):
                 message = "First pps booking passed and second pps booking failed due to tuner conflict"
                 print message
            else:
                 message =  "Testcase Failed: Booking Passed or Failed for both the events due to unexpected behaviour"
                 debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                 cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                 print message
                 tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                 return tims_dict
            print "### STEP4: Change the tuner quota to 2 and then try the 2nd booking and see if it succeeds ######################################################### \n\n"
            setTuner_result = set_numberoftuners(protocol,upm_host,upm_port,upm_headers1,householdid,timeout,"2")
            if setTuner_result == "PASS":
                new_tunerquota = get_numberoftuners(protocol,upm_host,upm_port,upm_headers,householdid,timeout)
                if new_tunerquota:
                      if new_tunerquota == "2":
                          print "Tuner Quota updated successfully to the new value"
                          PPSBooking_result,response1 = do_PPSbooking_returnresponse(port_pps,protocol,pps_host,householdid,pps_headers,payload,random_contentId_list[1],timeout,printflg=False)
                          if PPSBooking_result == "PASS" :
                               print "PPS booking is successful for the event contentId %s" %(random_contentId_list[1])
                               message = "Testcase Passed :PPS booking is successful after having sufficient tuner quota"
                               cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                               print message
                               tims_dict = update_tims_data(tims_dict,0,message,["TC861"])
                               return tims_dict
                          else:
                               responsecontent1 = json.loads(response1.content)
                               if (response1.status_code == 403) and (responsecontent1["message"] == "Tuner Conflict Detected"):
                                   message = "Testcase Failed: PPS Booking Failed with Tunerconflict after having sufficient tuner quota"
                                   debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                   cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                   print message
                                   tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                                   return tims_dict
                               else:
                                   message = "Testcase Failed: PPS Booking Failed with some other reason after having sufficient tuner quota"
                                   debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                                   cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                                   print message
                                   tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                                   return tims_dict
                      else:
                           message = "Testcase Failed: Count of Numberoftuners for the household is not as expected"
                           cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                           print message
                           tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                           return tims_dict
                else:
                     message = "Testcase Failed: Unable to Fetch the numberoftuners for the household"
                     cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                     print message
                     tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                     return tims_dict
            else:
                 message = "Testcase Failed: Unable to Modify the numberoftuners for the household"
                 cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                 print message
                 tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
                 return tims_dict
        except :
             cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
             message =  "Testcase Failed :Error Occured in Script " + PrintException(True)
             print message 
             tims_dict = update_tims_data(tims_dict,1,message,["TC861"])
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


