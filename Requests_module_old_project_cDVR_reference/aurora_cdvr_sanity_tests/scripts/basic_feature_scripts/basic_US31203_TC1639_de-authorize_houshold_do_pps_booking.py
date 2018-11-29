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

##########################################################################
# Test steps: De-authorize a household for Cloud DVR, ensure household can not create new bookings
# STEP1:  Ingest the catalog of 1 events without any start time in PostXml
# STEP2:  Get the list of enabled services for the household and check "CDVR_ENABLER" in this list
# STEP3:  Delete the "CDVR_ENABLER" using the function that uses the API
# STEP4:  Get the Contents for program list
# STEP5:  Do the PPS Booking of an event and Verify PPS Booking fails with Status Code 403 and Message Booking Not Authorized
##########################################################################

def doit(cfg, printflg=False):
    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        time_value = end_time - start_time
        time_value = round(time_value, 6)
        time_value = str(time_value)
        filename = cfg['test_results']['filename']
        data = {
            "config": {
                "labname": cfg['LABNAME'],
                "extraconf": str(cfg['EXTRACONF']),
                "gitrepo": cfg['GITREPO'],
                "gitlastcommit": cfg['GITLASTCOMMIT'],
                "description": cfg['lab-description']
               }
            }
        timsResults = JsonReadWrite(filename)
        timsResults.writeDictJson(data)
        status_value = []
        for key, val in dict.items(rc):
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
            name = os.path.basename(__file__)[:-3]
            # message will eventually be the last log message but this is a
            # proof of concept
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
            if (1 in status_value) or (3 in status_value):
                 return (1)
            elif (4 in status_value) or (2 in status_value):
                return (2)
            else:
                 return(0)
        else:
              print "status_value not present "
              return 1
    except:
          print "Error Occurred in Script \n"
          PrintException()
          return (1)

def doit_wrapper(cfg, printflg=False):

    message = ""
    status = 3
    tims_dict = {
                 "TC1639": ["US31203", message, status]
                }

    print "US31203: UseCase: Suspend a household"
    print "TC1639: De-authorize a household for Cloud DVR, ensure household can not create new bookings"

    try:
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test

        # Initialize the Variables
        timeout = 2
        serviceIdlist = []
        random_contentId = None
        catalogresponse = None
        cdvrservicelist = []

        # set values based on config
        households_needed = cfg['basic_feature']['households_needed']
        eventtitle = "event" + str(random.randint(1, 999))
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
        ci_host = cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
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
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts, upm_hosts))
        result = "Fail"
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0, householdlimit - 1)
        householdid = prefix + str(index)

        # Ingest the Catalog to the CI Host
        print "### STEP1: Ingest the catalog of 1 events  ##########################\n \n"
        post_time = time.time() + ingest_minimum_delay
        channel = ChannelLineup(BoundaryInMinutes=0)
        timeslotinminutes = cfg['test_channels']['longProgramLength'] 
        channel.add_to_lineup(serviceId=testchannel1, timeSlotLengthMinutes=timeslotinminutes, timeSlotCount=1, programIDPrefix=eventtitle)
        ingest_endtime = channel.postXmlData(ci_host, ci_port, startTime=post_time)
        channel.writeXmlFiles(startTime=post_time)
        print "Channel Ingest XML :\n" + str(channel)
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1639"])
        return tims_dict
    try:
        for (cmdc_host, pps_host, upm_host) in hostlist:
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,pps_port, protocol, pps_host, householdid, pps_headers, timeout)
            # Get the List of Enabled Services for the Household
            print "### STEP2: Get the list of enabled services for the household and check 'CDVR_ENABLER' in this list #############\n \n"
            householdservicelist = get_HouseholdEnabledServices(protocol, upm_host, upm_port, householdid, upm_headers, timeout)
            servicelist = json.loads(householdservicelist)
            print "Household Service List" + str(servicelist)

            # Compare the Total list of Enabled Services and the CDVRServices,
            # than form a final servicelist to use it in the functions further
            if servicelist:
                for element in servicelist:
                    if element in cdvrServices:
                        cdvrservicelist.append(element)
            else:
                message = "Testcase Failed: Unable to get the Enabled Services for the Household"
                print message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC1639"])
                return tims_dict

            # Delete the CDVR Service for the household
            print "### STEP3: Delete the 'CDVR_ENABLER' using the function that uses the API ############################\n \n"
            deleteserviceresult = delete_HouseholdEnabledService(protocol, upm_host, upm_port, householdid, cdvrservicelist, upm_headers, timeout)
            if deleteserviceresult == "PASS":
                print "Deleting the Service for the Household is successful"
            else:
                message = "Testtcase Failed: Unable to Delete the Household Enabledservices"
                print message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC1639"])
                return tims_dict

            # Get the Dictionary of ContentId and the values for PPS Booking
            print "### STEP4: Get the Contents for program list###########################\n \n"
            gridservicelistresponse = fetch_gridRequest_lessthancurrenttime(catalogueId, protocol, cmdc_host, cmdc_port, serviceIdlist, region, timeout, printflg)
            if gridservicelistresponse:
                contentId_dict_all = get_currentandfuture_contentIddict(gridservicelistresponse, eventtitle, ['title'])
                print "Current and Future Events from the Grid Response\n" + str(contentId_dict_all)
                if contentId_dict_all:
                    contentId_list = get_contentIdlist_allcontentiddict_channellineup(contentId_dict_all, printflg)
                    print "List of Events in sorted format\n" + str(contentId_list)
                    if len(contentId_list) >= 1:
                        try:
                            current_broadcasting_contentId1 = contentId_list[0][0]
                            contentIdlist = [current_broadcasting_contentId1]
                            current_broadcasting_contentId1_starttime = contentId_list[0][1]
                            print "### STEP5: Do the PPS Booking and verify it failes with proper error code and status code ###############\n \n "
                            for contentid in contentIdlist:
                                payload = """{
                                    "scheduleInstanceId" : "%s",
                                    "checkConflicts" : true,
                                    "pvr":"nPVR"
                                    }""" % (contentid)
                                result, response = do_PPSbooking_returnresponse(pps_port, protocol, pps_host, householdid, pps_headers, payload, contentid, timeout, printflg)
                                time.sleep(fetch_bookingcatalog_delay)
                                if result == "FAIL":
                                    responsecontent = json.loads(response.content)
                                    if (response.status_code == 403) and (responsecontent["message"] == "Booking Not Authorized"):
                                        message = "TestCase Passed : PPS Booking failed due to CDVR Service deleted for the Household and the ContentId is: " + contentid
                                        set_HouseholdEnabledService(protocol, upm_host, upm_port, householdid, cdvrservicelist, upm_headers, timeout)
                                        print message
                                        tims_dict = update_tims_data(tims_dict, 0, message, ["TC1639"])
                                        return tims_dict
                                    else:
                                        message = "TestCase Failed : PPS booking failed due to unexpected reason"
                                        set_HouseholdEnabledService(protocol, upm_host, upm_port, householdid, cdvrservicelist, upm_headers, timeout)
                                        print message
                                        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1639"])
                                        return tims_dict
                                else:
                                    message =  "TestCase Failed : PPS Booking happened with de-authorized household"
                                    set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                    print message
                                    tims_dict = update_tims_data(tims_dict,1,message,["TC1639"])
                                    return tims_dict
                        except:
                            message =  "Testcase Failed: Error Occurred in PPS Booking " + PrintException(True)
                            set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                            print message
                            tims_dict = update_tims_data(tims_dict,1,message,["TC1639"])
                            return tims_dict    
                    else:
                        message =  "Testcase Failed: Unable to form ContentId list from ContentId dictionary"
                        set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                        print message
                        tims_dict = update_tims_data(tims_dict,1,message,["TC1639"])
                        return tims_dict
                else:
                    message =  "Testcase Failed: Unable to Form ContentId dictionary from the Grid Response"
                    set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                    print message
                    tims_dict = update_tims_data(tims_dict,1,message,["TC1639"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Fetch Grid Response"
                set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC1639"])
                return tims_dict
    except:
        message =  "TestCase Failed : Error Occurred:" + PrintException(True)
        if cdvrservicelist:
            set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,cdvrservicelist,upm_headers,timeout)
        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC1639"])
        return tims_dict
        
if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    # read config file 
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

