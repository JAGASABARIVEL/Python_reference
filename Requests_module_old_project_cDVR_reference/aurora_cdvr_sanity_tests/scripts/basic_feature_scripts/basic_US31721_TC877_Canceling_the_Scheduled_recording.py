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
#Test Steps :Canceling the Scheduled recording
# STEP1: Ingest a catalog of series and event (series event required as precondition )of n minutes each
# STEP2: fetch the contentID for series and do the series booking 
# STEP3: fetch the contentID for event  and do the event booking 
# STEP4: fetch the booking catalog and check for the event in the booking catalog 
# STEP5: if event successfully booked , then delete the particular event
# STEP6: verify that the delete event was successful and gives the final verdict of the test case  
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
    try :
        message = ""
        status = 3
        tims_dict = {
                "TC877":[ "US31721",message,status]
                }
        print "\n US31721:Delete cDVR Bookings by Subscriber"
        print "\n TC877: Canceling the Scheduled recording" 

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
        random_contentIdDict = None
        bookedcatalogresponse = None
        deletePPSbooking = None
        result = "FAIL"

        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        port_pps = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        eventbooking_fetch_delay = cfg['pps']['fetch_bookingCatalog_delay']
        series_bookingstatecheck_waittime = cfg['pps']['series_bookingstatecheck_waittime']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        upm_hosts = [cfg['upm']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
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
        diskquota_headers_hh = {
            'Content-Type': 'text/plain',
            'Source-Type': 'WEB',
            'Source-ID': '211.209.128.25',
            }
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts))
        printLog("Final list :"+ str(hosts_list),printflg)
        title1 = 'Cancelsch1' + str(random.randint(1,249))
        title2 = 'Cancelsch2' + str(random.randint(250,499))
        title_list = [title1, title2]
        #Late post time such that series recording do not start
        print "### STEP1:Ingest a catalog of series and event (series event required as precondition) of n minutes each######################################### \n \n "
        seconds = 2
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        post_time = time.time() + (seconds * cfg['ci']['earliestSecondsFromNowToSchedule']) + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength']
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ci_ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes,showID=title1,episodeCount=2,startEpisodeNumber=1,timeSlotCount=2)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=2,programIDPrefix=title2)
        channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        length =channel.getTotalLength()
        print channel
        total_ci_ingest_delay = ingest_minimum_delay + length * ci_ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(total_ci_ingest_delay)
        time.sleep(total_ci_ingest_delay)
    except:
        message =  "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC877"])
        return tims_dict

    for (cmdc_host,pps_host) in hosts_list :
        try:
            print "### STEP2:fetch the contentID of series and do the series booking ############################################################ \n \n "
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
            gridservicelistresponse = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg)
            if gridservicelistresponse:
                contentId_dict_all = get_series_contentIddict_bytitle(gridservicelistresponse,title1,['title','seriesId','episodeNumber'])
                print "Series ContentId dictionary from the grid response\n" + str(contentId_dict_all)
                if contentId_dict_all:
                    series_contentId = sorted(contentId_dict_all.items(), key=lambda x:x[1])
                    print "Series ContentId list after sorting\n" +str(series_contentId)
                else:
                    message = "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    print  message
                    tims_dict = update_tims_data(tims_dict, 1, message, ["TC877"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Fetch Grid Response"
                print  message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC877"])
                return tims_dict
            if len(series_contentId) >= 2:
                random_contentId = series_contentId[0][0]
                payload = """{
                    "scheduleInstanceId" : "%s",
                    "checkConflicts" : true,
                    "pvr":"nPVR",
                    "recurrence":"SERIES"
                    }""" % (random_contentId)
                result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload,random_contentId,timeout,printflg)
            else:
                message ="Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                print message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC877"])
                return tims_dict
            if result == "PASS":
                print "PPS booking is successful for the series contentId %s" %(random_contentId)
            else:
                message = "Testcase Failed: PPS Booking failed for the series contentId %s" %(random_contentId) 
                print  message
                tims_dict = update_tims_data(tims_dict,1, message, ["TC877"])
                return tims_dict
            print "### STEP3:fetch the contentID for event  and do the event booking  ############################################################ \n \n "
            contentId_dict_all = get_contentIddict_bytitle(gridservicelistresponse,title2,['title'])
            print "Event ContentId dictionary from the grid response\n" + str(contentId_dict_all)
            if contentId_dict_all:
                event_contentId_list = sorted(contentId_dict_all.items(), key=lambda x:x[1])
                print "Event ContentId list after sorting\n" +str(series_contentId)
                if len(event_contentId_list) >0:
                    event_contentId = event_contentId_list[0][0]
                    event_payload = """{
                        "scheduleInstanceId" : "%s",
                        "checkConflicts" : true,
                        "pvr":"nPVR"
                        }""" % (event_contentId)
                    event_result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,event_payload,event_contentId,timeout,printflg)
                    if event_result == "PASS":
                        print "PPS booking is successful for the event contentId %s" %(event_contentId)
                    else:
                        message = "Testcase Failed: PPS Booking failed for the event contentId %s" %(event_contentId)
                        debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                        cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict, 1, message, ["TC877"])
                        return tims_dict
                else:
                    message ="Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict, 1, message, ["TC877"])
                    return tims_dict
            else:
                message ="Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC877"])
                return tims_dict
            print "### STEP4: check for the event in the booking catalog and delete the event,verify delete ########################################## \n \n "
            time.sleep(series_bookingstatecheck_waittime)
            time.sleep(eventbooking_fetch_delay)
            bookedcatalogresponse = fetch_bookingCatalog(port_pps,protocol,pps_host,householdid,timeout)
            if bookedcatalogresponse:
                event_state = json.loads(bookedcatalogresponse.content)
                for val in event_state:
                    if val["scheduleInstance"] == event_contentId :
                        if val["state"] == "BOOKED":
                            print "Event contentId in the Booked Catalog"
                            uri_delete = val['uri']
                            deletePPSbooking=delete_PPSbooking(port_pps,protocol,pps_host,pps_headers,timeout,uri_delete,printflg=False)
                        else:
                            message = "Testcase Failed: Testcase Failed: contentId is not in Booked Catalog"
                            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC877"])
                            return tims_dict
                if deletePPSbooking == "PASS":
                    message = "Testcase Passed: Scheduled recording of an Event got deleted successfully"
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,0,message,["TC877"])
                    return tims_dict
                else:
                    message = "Testcase Failed: Failed to delete the scheduled recording of an Event"
                    debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC877"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to fetch Booked Catalog"
                debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC877"])
                return tims_dict
        except:
            message = "Testcase Failed: Error Occured in Script " + PrintException(True)
            debug_print_log(port_pps,protocol,pps_host,householdid,timeout)
            cleanup_household(cfg,port_pps,protocol,pps_host,householdid,pps_headers,timeout)
            print message
            tims_dict = update_tims_data(tims_dict,1,message,["TC877"])
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




