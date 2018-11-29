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
################################################################################################################################################
# Teststeps: Do the Event Booking without Entitlement
# STEP1:  Ingest the catalog of 2 events without any start time in PostXml
# STEP2:  Get the list of enabled services for the household and check "CDVR_ENABLER" in this list
# STEP3:  Delete the "CDVR_ENABLER" using the function that uses the API
# STEP4:  Get the Contents for the current broadcasting and the future program
# STEP5:  Verify if the firstprogram start time is less than the current time and the second content start time is greater than the current time
# STEP6:  Do the PPS Booking of both the contents and verify the status code
# STEP7:  Enable the Service using the function that uses PUT in the same API
# STEP8:  Do the PPS Booking and verify if that is successful
# STEP9:  Verify the Booked Catalog and see if both the Events are present in the catalog
################################################################################################################################################
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
            if (1 in status_value) or (3 in status_value) :
                 return (1)
            elif (4 in status_value) or (2 in status_value):
                return (2)
            else:
                 return(0)
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
                 "TC892":["US31737",message,status]
                }
    '''
    Do the Event Booking without CDVR Entitlement and Verify after Enabling CDVR for household
    '''
    print "US31737: UseCase: Schedule Event based Recording"
    print "TC892: Booking an event for recording without entitlement"
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
        catalogresponse = None
        cdvrservicelist = []

        # set values based on config
        households_needed = cfg['basic_feature']['households_needed']
        eventtitle = "recwoent" + str(random.randint(1,999))
        upm_port = cfg['upm']['port']
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceIdlist.append(unicode(testchannel1))
        prefix = cfg['basic_feature']['household_prefix']
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        upm_hosts = [cfg['upm']['host']]
        fetch_bookingcatalog_delay = cfg['pps']['fetch_bookingCatalog_delay']
        cdvrServices = '"{0}"'.format('", "'.join(cfg['cdvrServices']))
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
        upm_headers = {
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Accept': 'application/json',
            }
        hostlist = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        result = "Fail"
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)

        #Ingest the Catalog to the CI Host
        print "### STEP1: Ingest the catalog of 2 events without any start time in PostXml ##########################\n \n" 
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        post_time = time.time() + ingest_minimum_delay
        timeslotinminutes = cfg['test_channels']['mediumProgramLength']
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=testchannel1,timeSlotLengthMinutes=timeslotinminutes,timeSlotCount=2,programIDPrefix = eventtitle)
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime=post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
    except:
        message =  "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
        return tims_dict

    try:
        for (cmdc_host,pps_host,upm_host) in hostlist :
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)

            #Get the List of Enabled Services for the Household
            print "### STEP2: Get the list of enabled services for the household and check 'CDVR_ENABLER' in this list #############\n \n"
            householdservicelist = get_HouseholdEnabledServices(protocol,upm_host,upm_port,householdid,upm_headers,timeout)
            servicelist = json.loads(householdservicelist)
            print "Household Service List" + str(servicelist)
            
            #Compare the Total list of Enabled Services and the CDVRServices, than form a final servicelist to use it in the functions further 
            if servicelist:
                for element in servicelist:
                    if element in cdvrServices:
                        cdvrservicelist.append(element)
            else:
                message =  "Testcase Failed: Unable to get the Enabled Services for the Household"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                return tims_dict
            #Delete the CDVR Service for the household
            print "### STEP3: Delete the 'CDVR_ENABLER' using the function that uses the API ############################\n \n"
            deleteserviceresult = delete_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
            if deleteserviceresult == "PASS":
                print "Deleting the Service for the Household is successful"
            else:
                message = "Testtcase Failed: Unable to Delete the Household Enabledservices"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                return tims_dict
            #Get the Dictionary of ContentId and the values for PPS Booking
            print "### STEP4: Get the Contents for the current broadcasting and the future program ###########################\n \n"
            gridservicelistresponse = fetch_gridRequest_lessthancurrenttime(catalogueId,protocol,cmdc_host,cmdc_port,serviceIdlist,region,timeout,printflg)
            if gridservicelistresponse:
                contentId_dict_all = get_currentandfuture_contentIddict(gridservicelistresponse,eventtitle,['title'])
                print "ContentId dictionary from the grid response\n" + str(contentId_dict_all)
                if contentId_dict_all:
                    contentId_list = get_contentIdlist_allcontentiddict_channellineup(contentId_dict_all,printflg)
                    print "ContentId list after sorting\n" + str(contentId_list)
                    if len(contentId_list) > 1:
                        current_broadcasting_contentId1 = contentId_list[0][0]
                        future_booking_contentId2 = contentId_list[1][0]
                        contentIdlist = [current_broadcasting_contentId1,future_booking_contentId2]
                        print "### STEP5: Verify if the firstprogram start time is less than the current time and the second content start time is greater than the current time ##########\n \n"
                        current_broadcasting_contentId1_starttime = contentId_list[0][1]
                        future_booking_contentId2_startime = contentId_list[1][1]
                        print "### STEP6: Do the PPS Booking of both the contents and verify the status code ###############\n \n "
                        for contentid in contentIdlist:
                            payload = """{
                                "scheduleInstanceId" : "%s",
                                "checkConflicts" : true, 
                                "pvr":"nPVR"
                                }""" % (contentid)
                            result,response = do_PPSbooking_returnresponse(pps_port,protocol,pps_host,householdid,pps_headers,payload,contentid,timeout,printflg)
                            time.sleep(fetch_bookingcatalog_delay)
                            if result == "FAIL":
                                responsecontent = json.loads(response.content)
                                if (response.status_code == 403) and (responsecontent["message"] == "Booking Not Authorized"):
                                    print "PPS Booking failed due to CDVR Service deleted for the Household and the ContentId is: " + contentid
                                else:
                                    message =  "Testcase Failed: PPS Booking failed due to unexpected reason"
                                    set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                                    print message      
                                    tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                                    return tims_dict
                            else:
                                message =  "Testcase Failed: Able to do the PPS Booking without the CDVR Enabled Services for a Household"
                                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                                print message
                                tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                                return tims_dict
                    else:
                        message =  "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                        set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                        return tims_dict
                else:
                    message =  "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                    set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                    return tims_dict
            else:
                message =  "Testcase Failed: Unable to Fetch Grid Response"
                set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                return tims_dict
            
            #Enable the CDVR for the Household and try the PPS Booking
            print "#### STEP7:  Enable the Service using the function that uses PUT in the same API ###########################\n \n"
            enableserviceresult = set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
            bookingpasscounter = 0
            if enableserviceresult == "PASS":
                print "### STEP8: Do the PPS Booking and verify if that is successful #############################\n \n" 
                for contentid in contentIdlist:
                    payload = """{
                        "scheduleInstanceId" : "%s",
                        "checkConflicts" : true,
                        "pvr":"nPVR"
                        }""" % (contentid)
                    result,response = do_PPSbooking_returnresponse(pps_port,protocol,pps_host,householdid,pps_headers,payload,contentid,timeout,printflg)
                    time.sleep(fetch_bookingcatalog_delay)
                    if result == "PASS":
                        print "PPS booking is successful for the event contentId %s" %(contentid)
                        bookingpasscounter += 1
                    else:
                        message =  "Testcase Failed: PPS Booking failed for the event contentId %s" %(contentid)
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                        return tims_dict
            else:
                message =  "Testcase Failed: Unable to Set the Service for the Household"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                return tims_dict

            #Verify the Booked Catalog after the Successful PPS Booking
            print "### STEP9: Verify the Booked Catalog and see if both the Events are present in the catalog ###############\n \n"
            bookedeventcounter = 0
            if bookingpasscounter == 2:
                bookedcatalogresult,catalogresponse = verify_booking(pps_port,protocol,pps_host,householdid,contentIdlist,timeout)
                if bookedcatalogresult == "PASS" and catalogresponse:
                    message =  "Testcase Passed: PPS Booking successful and Verified the Booked Catalog"
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,0,message,["TC892"])
                    return tims_dict
                else:
                    message =  "Testcase Failed: Unable to Verify Booked Catalog"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                    return tims_dict
            else:
                message =  "Booked Catalog Events are not matching with the Actual PPS Booking one"
                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
                return tims_dict                                             
    except:
        message =  "Testcase Failed: Error Occurred in Script " + PrintException(True)
        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
        if cdvrservicelist:
            set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC892"])
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

