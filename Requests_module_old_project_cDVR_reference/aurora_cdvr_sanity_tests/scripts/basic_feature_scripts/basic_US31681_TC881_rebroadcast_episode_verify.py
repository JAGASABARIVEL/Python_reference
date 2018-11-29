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
##########################################################################
# TC881: Prevent duplicate recordings in household catalog
# STEP1:Ingest a series of 3 episodes of n minutes duration and ingest an episode into the same series of n minutes Duration with same title. 
# STEP2:Fetch the grid response and perform the series booking
# STEP3:Fetch the booked catalog to check whether the rebroadcasted episode is not present in the booked catalog
# STEP4:Fetch the recorded library to check whether the rebroadcasted episode is not present in the recorded library 
##############################################################################################################################################
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

def doit_wrapper(cfg,printflg=False):
   try :
        message = ""
        status = 3
        tims_dict = {
            "TC881": ["US31681", message, status]
           }
        print "US31681: As a Viewer, I want to prevent duplicate copies of an episode within a series from being recorded"
        print "TC881: Prevent duplicate recordings in household catalog"
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        #Initialize the Variables
        timeout = 2
        serviceIdlist = []
        random_contentId = None
        randomcontentidlist = []
        recIdlist =[]
        gridservicelistresponse =None
        jsonbookedcatalog =None
        recorded_lib =None
        series_grid_episodes =None 

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
        testchannel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        serviceIdlist.append(unicode(testchannel2))
        prefix = cfg['basic_feature']['household_prefix']
        throttle_milliseconds = cfg['basic_feature']['throttle_milliseconds']
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']
        series_bookingstatecheck = cfg['pps']['series_bookingstatecheck_waittime']
        # Do PPS Booking
        if (cmdc_hosts == None) or ( pps_hosts == None) :
            tims_dict = update_tims_data(tims_dict, 3, message, ["TC881"])
            return tims_dict
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
        result = "Fail"
        print "### STEP1:Ingest a series of 3 episodes of n minutes duration and ingest an episode into the same series of 2 minutes Duration with same title. ###########################\n\n"
        title = 'repeatepi' + str(random.randint(600,699))
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ci_ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ci_ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        seconds = 1
        episode_post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ci_ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength'] + roundofftonextint(recordingstatecheck_waittime)
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=testchannel2,timeSlotLengthMinutes=timeslotinminutes,showID=title,startEpisodeNumber=1,episodeCount=2,timeSlotCount=2)
        channel.add_to_lineup(serviceId=testchannel2,timeSlotLengthMinutes=timeslotinminutes,showID=title,startEpisodeNumber=1,episodeCount=1,timeSlotCount=1)
        End_broadcast_time =channel.postXmlData(ci_host,ci_port,startTime = episode_post_time)
        channel.writeXmlFiles(startTime = episode_post_time)
        length =channel.getTotalLength() 
        print channel
        total_ci_ingest_delay = ci_ingest_minimum_delay + length * ci_ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(total_ci_ingest_delay)
        time.sleep(total_ci_ingest_delay)
        for (cmdc_host,pps_host) in hostlist :
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            result,message = series_booking(cfg,catalogueId,pps_port,protocol,pps_host,householdid,pps_headers,cmdc_host,cmdc_port,serviceIdlist,region,timeout,title,End_broadcast_time,series_bookingstatecheck,recordedstatecheck_waittime,printflg)
            if result == "PASS":
                tims_dict = update_tims_data(tims_dict,0, message, ["TC881"])
                return tims_dict
            else:
                tims_dict = update_tims_data(tims_dict,1, message, ["TC881"])
                return tims_dict
   except:
        message =  "Testcase Failed: Error Occurred in Script " + PrintException(True)
        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
        print  message
        tims_dict = update_tims_data(tims_dict,1, message, ["TC881"])
        return tims_dict

def series_booking(cfg,catalogueId,pps_port,protocol,pps_host,householdid,pps_headers,cmdc_host,cmdc_port,serviceIdlist,region,timeout,title,End_broadcat_time,series_bookingstatecheck,recordedstatecheck_waittime,printflg):
    try :
        print "### STEP2:Fetch the grid response and perform the series booking#############################################\n\n"
        gridservicelistresponse = fetch_gridRequest(catalogueId,protocol,cmdc_host,cmdc_port,serviceIdlist,region,timeout,printflg)
        if gridservicelistresponse:
            contentId_dict_all = get_series_contentIddict_bytitle(gridservicelistresponse,title,['title','seriesId','episodeNumber'])
            print "Series ContentId dictionary from the Grid Response\n" + str(contentId_dict_all)
            if contentId_dict_all :
                series_contentId = sorted(contentId_dict_all.items(), key=lambda x:x[1])
                print "Series contentId list after sorting\n" + str(series_contentId)
                if len(series_contentId) >2:
                    firstepisode_contentId = series_contentId[0][0]
                    secondepisode_contendId = series_contentId[1][0]
                    rebroadcast_contentId = series_contentId[2][0]
                    rebroadcasted_episode_details = series_contentId[2][1]
                    rebroadcast_episode_endtime = series_contentId[2][1][1]
                    series_contentidlist = [firstepisode_contentId,secondepisode_contendId]
                    payload = """{
                        "scheduleInstanceId" : "%s",
                        "checkConflicts" : true, 
                        "pvr":"nPVR",
                        "recurrence":"SERIES"
                        }""" % (firstepisode_contentId)
                    print "Current system time before pps booking " + str(time.time())
                    result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,payload,firstepisode_contentId,timeout,printflg)
                    if result == "PASS":
                        print "PPS booking is successful for the series with contentId %s" %(firstepisode_contentId)
                        time.sleep(series_bookingstatecheck)
                        print"### STEP3:Fetch the booked catalog to check whether the rebroadcasted episode is not present in the booked catalog####################\n\n"
                        booked_result,booked_msg = check_bookedlib_for_rebroadcasted_episode(pps_port,protocol,pps_host,householdid,timeout,series_contentidlist,rebroadcast_contentId)
                        if booked_result == "PASS" :
                            End_broadcat_wait_time = get_timedifference(rebroadcast_episode_endtime,printflg)
                            print "System waits till %s Seconds for Rebroadcasted episode end time" %(End_broadcat_wait_time)
                            time.sleep(End_broadcat_wait_time)
                            time.sleep(recordedstatecheck_waittime)
                            print "### STEP4:Fetch the recorded library to check whether the rebroadcasted episode is not present in the recorded library ###########################\n\n" 
                            recorded_result,recorded_msg = check_recordedlib_for_rebroadcasted_episode(protocol,pps_host,pps_port,householdid,timeout,series_contentidlist,rebroadcast_contentId)
                            if recorded_result == "PASS" :
                                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                message =  "Testcase Passed: " + recorded_msg
                                print message
                                return("PASS",message)
                            else:
                                message =  "Testcase Failed: " + recorded_msg
                                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                print message
                                return("FAIL",message)
                        else:
                            message = "Testcase Failed: " + booked_msg
                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            return("FAIL",message)
                    else:
                        message = "Testcase Failed: PPS Booking failed for the series contentId %s" %(firstepisode_contentId)
                        debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                        print  message
                        return ("FAIL",message)
                else:
                    message ="Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                    print message
                    return ("FAIL",message)
            else:
                message = "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                print  message
                return ("FAIL",message)
        else:
            message = "Testcase Failed: Unable to Fetch Grid Response"
            print  message
            return ("FAIL",message)
    except:
           message = "Testcase Failed: Error Occurred in Script "  + PrintException(True)
           print  message
           return ("FAIL",message)
def check_bookedlib_for_rebroadcasted_episode(pps_port,protocol,pps_host,householdid,timeout,series_contentidlist,rebroadcast_contentId):
    try :
        bookedcatalogresult,bookedcatalogresponse = verify_booking(pps_port,protocol,pps_host,householdid,rebroadcast_contentId,timeout)
        if bookedcatalogresult == "FAIL":
            bookedcatalogresult1,bookedcatalogresponse1 = verify_booking(pps_port,protocol,pps_host,householdid,series_contentidlist,timeout)
            if bookedcatalogresult1 == "PASS":
                message ="Rebroadcasted Episode is not in booked library"
                print message
                return ("PASS",message)
            else:
                message = "Unable to Verify Booked Catalog"
                return ("FAIL",message)
        else:
            message = "Rebroadcasted Episode is present in the Booked Library"
            return("FAIL",message) 
    except:
        message =  "Error Occurred in Script " + PrintException(True)
        return("FAIL",message)
def check_recordedlib_for_rebroadcasted_episode(protocol,pps_host,pps_port,householdid,timeout,series_contentidlist,rebroadcast_contentId):
    try :
        recordedcatalogresult,recordedcatalogresponse = verify_recorded_state(pps_port,protocol,pps_host,householdid,rebroadcast_contentId,timeout)
        if recordedcatalogresult == "FAIL":
            recordedcatalogresult1,recordedcatalogresponse1 = verify_recorded_state(pps_port,protocol,pps_host,householdid,series_contentidlist,timeout)
            if recordedcatalogresult1 == "PASS":
                message ="Rebroadcasted Episode is not in Recorded library which is not expected"
                return ("PASS",message)
            else:
                message = "Unable to Verify Recorded Catalog"
                return ("FAIL",message)
        else:
            message = "Rebroadcasted Episode is present in the Recorded Library which is not expected"
            return("FAIL",message) 
    except:
        message =  "Error Occurred in Script " + PrintException(True)
        return("FAIL",message)
    
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

