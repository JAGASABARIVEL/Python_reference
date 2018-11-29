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

###################################################################################################################################
# TC1647: Re-authorize a household for Cloud DVR, ensure Storage Quota and Recording Tuner Quota values remain unchanged
#STEP1: Get the Tuner and Storage Quota value of an household and store it
#STEP2: Disable the CDVR services for the same household for 1 minute
#STEP3: Enable the CDVR services and Verify
#STEP4: Get the Tuner and Storage Quota value of an household and confirm that it is same as Step1
#STEP5: Enable back all the Services irrespective of pass or fail 
####################################################################################################################################

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
                "gitlastcommit":  cfg['GITLASTCOMMIT'],
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
        "TC1647": ["US31202", message, status]
    }
    print "US31202: Suspend a household"
    print "TC1647: Re-authorize a household for Cloud DVR, ensure Storage Quota and Recording Tuner Quota values remain unchanged"
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
        prefix = cfg['basic_feature']['household_prefix']
        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        upm_hosts = [cfg['upm']['host']]
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
        upm_headers = {
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Accept': 'application/json',
            }
        tuner_headers = {
            'Content-Type': 'text/plain',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Accept': 'text/plain',
            }
        hostlist = list(itertools.product(cmdc_hosts, pps_hosts, upm_hosts))
        result = "Fail"
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0, householdlimit - 1)
        householdid = prefix + str(index)
        cdvr_service_list= ["CDVR","ALLOW-CDVR-TIME-BASED-RECORDING"]
        print "CDVR Service List: " + str(cdvr_service_list)
    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1647"])
        return tims_dict
    try:
        for (cmdc_host, pps_host, upm_host) in hostlist:
            print "\n\n###STEP1: Get the Tuner and Storage Quota value of an household and store it #####################################################################\n"
            default_disk_quota = fetch_full_details_diskquota(
                protocol, upm_host, upm_port, householdid, timeout, printflg)
            tuners_in_hh = get_numberoftuners(
                protocol, upm_host, upm_port, tuner_headers, householdid, timeout)
            default_disk_quota = json.loads(default_disk_quota.content)
            default_tuner_quota = int(tuners_in_hh)
            print "Default Tuner value fetched from household : " , default_tuner_quota
            print "Default DiskQuota value fetched from household : ", default_disk_quota
            print "\n\n###STEP2: Disable the CDVR services for the same household for 1 minute #############################################################\n"
            deleteserviceresult = delete_HouseholdEnabledService(
                  protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
            if deleteserviceresult == "PASS":
                 print "Deleting the Service for the Household is successful, will wait for 1 minute before re enabling the services."                     
                 time.sleep(60)
            else:
                 message = "Testtcase Failed: Unable to Delete the Household Enabledservices"
                 print message
                 tims_dict = update_tims_data(
                           tims_dict, 1, message, ["TC1647"])
                 return tims_dict
            householdservicelist = get_HouseholdEnabledServices(
                protocol, upm_host, upm_port, householdid, upm_headers, timeout)
            if householdservicelist:
                servicelist = json.loads(householdservicelist)
                print "Household Service List" + str(servicelist)
                for services in cdvr_service_list:
                    if services in servicelist:
                       message = "Testcase failed :CDVR services are present in the household enabled services after deletion"
                       set_HouseholdEnabledService(
                           protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                       print message
                       tims_dict = update_tims_data(
                           tims_dict, 1, message, ["TC1647"])
                       return tims_dict
            else:
                message = "Testcase Failed: Unable to get the Enabled Services for the Household"
                set_HouseholdEnabledService(
                    protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                print message
                tims_dict = update_tims_data(
                    tims_dict, 1, message, ["TC1647"])
                return tims_dict
            print "\n\n###STEP3: Enable the CDVR services and Verify ##########################################################\n"
            set_Household_enable_services = set_HouseholdEnabledService(
                protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
            if set_Household_enable_services:
                householdservicelist = get_HouseholdEnabledServices(
                    protocol, upm_host, upm_port, householdid, upm_headers, timeout)
                if householdservicelist:
                    cdvr_list_after_enable = 0 
                    servicelist = json.loads(householdservicelist)
                    print "Household Service List" + str(servicelist)
                    for service in cdvr_service_list:
                         if service in servicelist:
                            cdvr_list_after_enable = cdvr_list_after_enable + 1
                    if cdvr_list_after_enable:
                        if cdvr_list_after_enable == len(cdvr_service_list):
                            print "CDVR services are enabled successfully"
                            print "\n\n###STEP4: Get the Tuner and Storage Quota value of an household and confirm that it is same as Step1 ############################################\n"
                            disk_quota = fetch_full_details_diskquota(
                                protocol, upm_host, upm_port, householdid, timeout, printflg)
                            tuners_in_hh = get_numberoftuners(
                                protocol, upm_host, upm_port, tuner_headers, householdid, timeout)
                            disk_quota = json.loads(disk_quota.content)
                            tuners_in_hh = int(tuners_in_hh)
                            print "Tuner value fetched from household : " , tuners_in_hh
                            print "DiskQuota value fetched from household : ", disk_quota                            
                        else:
                            message = "Testcase failed :CDVR services are not enabled successfully"
                            set_HouseholdEnabledService(
                                protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                            print message
                            tims_dict = update_tims_data(
                                tims_dict, 1, message, ["TC1647"])
                            return tims_dict
                        print "\n\n###STEP5: Enable back all the Services irrespective of pass or fail ##########################################################################\n"
                        if (tuners_in_hh == default_tuner_quota) and (disk_quota == default_disk_quota):
                            message = "Testcase Passed: Tunerquota and Diskquota values remain same after enabling the household services"
                            set_HouseholdEnabledService(
                                protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                            print message
                            tims_dict = update_tims_data(
                                tims_dict, 0, message, ["TC1647"])
                            return tims_dict
                        else:
                            message = "Testcase Failed: Tunerquota and Diskquota values does not remain same after enabling the household services"
                            set_HouseholdEnabledService(
                                protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                            print message
                            tims_dict = update_tims_data(
                                tims_dict, 1, message, ["TC1647"])
                            return tims_dict           
                    else:
                        message = "Testcase Failed: Unable to fetch the cdvr Service list for the Household after enabling"
                        set_HouseholdEnabledService(
                            protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                        print message
                        tims_dict = update_tims_data(
                            tims_dict, 1, message, ["TC1647"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to get the Enabled Services for the Household"
                    set_HouseholdEnabledService(
                        protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                    print message
                    tims_dict = update_tims_data(
                        tims_dict, 1, message, ["TC1647"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Set the Service for the Household"
                set_HouseholdEnabledService(
                    protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                print message
                tims_dict = update_tims_data(
                    tims_dict, 1, message, ["TC1647"])
                return tims_dict
    except:
        message = "Testcase Failed: Error Occurred in Script " + PrintException(True)
        if cdvr_service_list:
            set_HouseholdEnabledService(
                protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1647"])
        return tims_dict

if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    # read config file
    sa = sys.argv
    cfg = relative_config_file(sa, scriptName)
    if cfg['basic_feature']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
        print
    L = doit_wrapper(cfg, True)
    status_value = []
    for key, val in dict.items(L):
        status_value.append(val[2])
    if status_value:
        if (1 in status_value) or (3 in status_value):
            exit(1)
        else:
            exit(0)
    else:
        exit(1)
