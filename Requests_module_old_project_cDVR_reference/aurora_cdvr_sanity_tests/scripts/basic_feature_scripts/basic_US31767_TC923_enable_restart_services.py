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
# Teststeps: Do the Event Booking without Entitlement
# STEP1:  Get the list of enabled services for the household and check "Restart" in this list
# STEP2:  Delete the "Restart" using the function that uses the API
# STEP3:  Get the list of enabled services and check wheather the restart services is deleted or not
# STEP4:  enable the restart services and verify it
##########################################################################


def doit(cfg, printflg=False):
    try:
        start_time = time.time()
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
        "TC923": ["US31767", message, status]
    }
    '''
    Do the Event Booking without CDVR Entitlement and Verify after Enabling CDVR for household
    '''
    print "US31767: As a SP, I want an API so I can enable RestartTV service entitlement for a subscriber via my Billing System."
    print "TC923: Restart TV: an API is available to enable Restart TV service entitlement"
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
        sub = 'RESTART'
    except:
        message = "Testcase Failed: Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC923"])
        return tims_dict

    try:
        for (cmdc_host, pps_host, upm_host) in hostlist:
            # Get the List of Enabled Services for the Householdi
            print "###STEP1:  Get the list of enabled services for the household and check Restart in this list ##########################\n\n"
            householdservicelist = get_HouseholdEnabledServices(
                protocol, upm_host, upm_port, householdid, upm_headers, timeout)
            if householdservicelist:
                servicelist = json.loads(householdservicelist)
                print "Household Service List" + str(servicelist)
                restart_service_list = [
                    x for x in servicelist if re.search(sub, x)]
                if restart_service_list:
                    print restart_service_list
                    print "###STEP2:  Delete the Restart using the function that uses the API ##########################\n\n"
                    deleteserviceresult = delete_HouseholdEnabledService(
                        protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
                    if deleteserviceresult == "PASS":
                        print "Deleting the Service for the Household is successful"
                    else:
                        message = "Testtcase Failed: Unable to Delete the Household Enabledservices"
                        print message
                        tims_dict = update_tims_data(
                            tims_dict, 1, message, ["TC923"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to fetch the Restart Service list  for the Household"
                    print message
                    tims_dict = update_tims_data(
                        tims_dict, 1, message, ["TC923"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to get the Enabled Services for the Household"
                print message
                tims_dict = update_tims_data(
                    tims_dict, 1, message, ["TC923"])
                return tims_dict
            print "###STEP3:  Get the list of enabled services and check wheather the restart services is deleted or not ##########################\n\n"
            householdservicelist = get_HouseholdEnabledServices(
                protocol, upm_host, upm_port, householdid, upm_headers, timeout)
            if householdservicelist:
                servicelist = json.loads(householdservicelist)
                print "Household Service List" + str(servicelist)
                restart_list_after_deletion = [
                    x for x in servicelist if re.search(sub, x)]
                if restart_list_after_deletion:
                    message = "Testcase Failed :RESTART services are present in the household enable services after deletion"
                    set_HouseholdEnabledService(
                        protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
                    print message
                    tims_dict = update_tims_data(
                        tims_dict, 1, message, ["TC923"])
                    return tims_dict
                else:
                    print "RESTART services are not present in the household enable services after deletion"
            else:
                message = "Testcase Failed: Unable to get the Enabled Services for the Household"
                set_HouseholdEnabledService(
                    protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
                print message
                tims_dict = update_tims_data(
                    tims_dict, 1, message, ["TC923"])
                return tims_dict
            print "###STEP4:  enable the restart services and verify it ##########################\n\n"
            set_Household_enable_services = set_HouseholdEnabledService(
                protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
            if set_Household_enable_services:
                householdservicelist = get_HouseholdEnabledServices(
                    protocol, upm_host, upm_port, householdid, upm_headers, timeout)
                if householdservicelist:
                    servicelist = json.loads(householdservicelist)
                    print "Household Service List" + str(servicelist)
                    restart_list_after_enable = [
                        x for x in servicelist if re.search(sub, x)]
                    if restart_list_after_enable:
                        if len(restart_list_after_enable) == len(restart_service_list):
                            message = "Testcase Passed: RESTART services are enabled successfully"
                            set_HouseholdEnabledService(
                                protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
                            print message
                            tims_dict = update_tims_data(
                                tims_dict, 0, message, ["TC923"])
                            return tims_dict
                        else:
                            message = "Testcase Failed: RESTART services are not enabled successfully"
                            set_HouseholdEnabledService(
                                protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
                            print message
                            tims_dict = update_tims_data(
                                tims_dict, 1, message, ["TC923"])
                            return tims_dict
                    else:
                        message = "Testcase Failed: Unable to fetch the Restart Service list  for the Household"
                        set_HouseholdEnabledService(
                            protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
                        print message
                        tims_dict = update_tims_data(
                            tims_dict, 1, message, ["TC923"])
                        return tims_dict
                else:
                    message = "Testcase Failed: Unable to get the Enabled Services for the Household"
                    set_HouseholdEnabledService(
                        protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
                    print message
                    tims_dict = update_tims_data(
                        tims_dict, 1, message, ["TC923"])
                    return tims_dict
            else:
                message = "Testcase Failed: Unable to Set the Service for the Household"
                set_HouseholdEnabledService(
                    protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
                print message
                tims_dict = update_tims_data(
                    tims_dict, 1, message, ["TC923"])
                return tims_dict
    except:
        message = "Testcase Failed: Error Occurred in Script " + PrintException(True)
        if restart_service_list:
            set_HouseholdEnabledService(
                protocol, upm_host, upm_port, householdid, restart_service_list, upm_headers, timeout)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC923"])
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
