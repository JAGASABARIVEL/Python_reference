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
# Teststeps: Canceling the Series
# STEP1:Ingesting a catalog for a  series of 3 episodes,each of n min
# STEP2:Getting the ContentId List for the series and doing the booking
# STEP3:Checking all the episodes of the series in the booking catalog and getting the neccessary details
# STEP4:Deleting only the first booked episode of the series and verifying it in the booking catalog 
# STEP5:Deleting all the remaining booked episode of the series and verifying it in the booking catalog
##########################################################################
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
        "TC891": ["US31774", message, status]
    }
    print "US31774: As a viewer, I want the ability to delete a series booking"
    print "TC891: Canceling the series"

    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    
    #Initialize the Variables
    index = 0
    timeout = 2
    serviceidlist = []
    random_contentId = None
    errorcount = 0
    randomcontentidlist = []
    recIdlist =[]
    gridservicelistresponse =None
    contentId_dict_all =None
    contentIdlist =None
    jsonbookedcatalog =None
 
    # set values based on config
    try:
        upm_host = cfg['upm']['host']
        pps_hosts = [cfg['pps']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        households_needed = cfg['basic_feature']['households_needed']
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        prefix = cfg['basic_feature']['household_prefix']
        throttle_milliseconds = cfg['basic_feature']['throttle_milliseconds']
        seriesbookingstatecheckwaittime = cfg['pps']['series_bookingstatecheck_waittime']
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
        #Late post time such that series recording do not start

        print "###STEP1:Ingesting a catalog for a  series of 3 episodes,each of n min ################################################### \n \n "
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        seconds = 1
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength']
        title = 'Canseries' + str(random.randint(600,699))
        channel = ChannelLineup(BoundaryInMinutes=1)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=3,showID=title,startEpisodeNumber=1,episodeCount=3, timeSlotCount=3)
        channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        length = channel.getTotalLength()
        print channel
        sleep_time = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_time)
        time.sleep(sleep_time)
    except:
        message ="Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print  message
        tims_dict = update_tims_data(tims_dict,1, message, ["TC891"])
        return tims_dict
    for (cmdc_host,pps_host) in hostlist :
        try:
            print "### Cleaning up the household at the beginning###################################"
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)

            print "###STEP2:Getting the ContentId List for the series and doing the booking################################## \n \n" 
            gridservicelistresponse = fetch_gridRequest(catalogueId,protocol,cmdc_host,cmdc_port,serviceidlist,region,timeout,printflg)
            if gridservicelistresponse:
                contentId_dict_all = get_series_contentIddict_bytitle(gridservicelistresponse,title,['title','seriesId','episodeNumber'])
                print "ContentId dictionary from the grid response\n" + str(contentId_dict_all)
                if contentId_dict_all :
                    contentIdlist = get_contentIdlist_groupbyseries(contentId_dict_all,printflg)
                    print "ContentId list after sorting\n" + str(contentIdlist)
                    if len(contentIdlist)>0:
                        random_contentId = contentIdlist[0][0]
                        seriesId = contentIdlist[0][2]
                        payload = """{
                            "scheduleInstanceId" : "%s",
                            "checkConflicts" : true, 
                            "pvr":"nPVR",
                            "recurrence":"SERIES"
                            }""" % (random_contentId)
                        result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,payload,random_contentId,timeout,printflg)
                        if result == "PASS":
                            print "PPS booking is successful for the series contentId %s" %(random_contentId)
                        else:
                            message = "Testcase Failed: PPS Booking failed for the series contentId %s" %(random_contentId)
                            debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                            print  message
                            tims_dict = update_tims_data(tims_dict,1, message, ["TC891"])
                            return tims_dict
                    else:
                        message = "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                        print  message
                        tims_dict = update_tims_data(tims_dict, 1, message, ["TC891"])
                        return tims_dict
                else:
                    message ="Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    print  message
                    tims_dict = update_tims_data(tims_dict, 1, message, ["TC891"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Fetch Grid Response"
                print  message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC891"])
                return tims_dict

            print "###STEP3:Checking all the episodes of the series in the booking catalog and getting the neccessary details############################ \n \n " 
            time.sleep(seriesbookingstatecheckwaittime)
            jsonbookedcatalog = fetch_bookingCatalog(pps_port,protocol,pps_host,householdid,timeout)
            if jsonbookedcatalog: 
                book_catalog=(json.dumps(json.loads(jsonbookedcatalog.content),indent = 4, sort_keys = False))
                episodes = booked_episodes(seriesId,jsonbookedcatalog)
                print "Booked Episodes %s"%episodes
                if episodes:
                    if len(episodes) == 3:
                        episode_detail =episodes.values()
                        first_episode_uri = episode_detail[0][4]
                        second_episode_uri = episode_detail[1][4]
                        first_episode_contentid = episode_detail[0][6]
                        second_episode_contentid = episode_detail[1][6]
                        third_episode_contentid = episode_detail[2][6]
                    else:
                        message = "Testcase Failed: Count of Episodes is not much as expected"
                        debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                        print  message
                        tims_dict = update_tims_data(tims_dict, 1, message, ["TC891"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to Fetch Booked Episodes"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    print  message
                    tims_dict = update_tims_data(tims_dict, 1, message, ["TC891"])
                    return tims_dict
            else:
                message ="Testcase Failed: Unable to fetch Booked Catalog"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print  message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC891"])
                return tims_dict

            print "###STEP4:Deleting only the first booked episode of the series and verifying it in the booking catalog########################## \n \n "
            deletePPSbooking = delete_PPSbooking(pps_port,protocol,pps_host,pps_headers,timeout,first_episode_uri,printflg=False)
            if deletePPSbooking == "PASS":
                print "First Booked Episode deleted successfully"
                bookedcatalogresult,bookedcatalogresponse = verify_booking(pps_port,protocol,pps_host,householdid,first_episode_contentid,timeout)
            else:
                message = "Testcase Failed: Unable to Delete Booked Event"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC891"])
                return tims_dict
            if bookedcatalogresult == "FAIL":
                print "First Episode is not present in the booked catalog is successfully verified"
            else:
                message ="Testcase Failed: Unable to Verify Booked Catalog"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print  message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC891"])
                return tims_dict

            print "###STEP5:Deleting all the remaining booked episode of the series and verifying it in the booking catalog########################## \n \n  "
            deleteSeriesbookingresult = delete_seriesbookings(pps_port,protocol,pps_host,pps_headers,timeout,second_episode_uri,printflg=False)
            if deleteSeriesbookingresult == "PASS"  :
                print "All Booked Episodes of the series are deleted from the library"
                bookedcatalogresult1,bookedcatalogresponse1 = verify_booking(pps_port,protocol,pps_host,householdid,[second_episode_contentid,third_episode_contentid],timeout)
                if bookedcatalogresult1 == "PASS":
                    message = "Testcase Failed: Unable to Verify Booked Catalog"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1, message, ["TC891"])                 
                    return tims_dict
                else:
                    message = "Testcase Passed: Deleted booked episodes have been removed from the  booked catalog successfully"
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,0, message, ["TC891"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Delete Series Bookings"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1, message, ["TC891"])
                return tims_dict
        except:
            message ="Testcase Failed: Error Occurred in Script " + PrintException(True)
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            print  message
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC891"])
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

