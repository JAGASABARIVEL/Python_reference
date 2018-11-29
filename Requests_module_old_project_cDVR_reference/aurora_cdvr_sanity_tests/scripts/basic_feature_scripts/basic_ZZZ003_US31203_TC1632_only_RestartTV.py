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
# TC1632 :Create a household authorized for RestartTV only
# STEP1:Delete the household if it exists or create the Household if it does not exist with only Restart Service
# STEP2:Fetch the the household Enabled Services and set only restart enable services
# STEP3:Verify that it has only Restart Service
# STEP4:Fetch the Diskquota and Tunerquota of the household
# STEP5:Verify that the default and fetched Tunerquota  and Diskquota are same
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
                return 1
            else:
                return 0
        else:
            print "status_value not present,Error in return code "
            return 1
    except:
        print "Error Occurred in Script \n"
        PrintException()
        return (1)

def doit_wrapper(cfg, printflg=False):
    message = ""
    status = 3
    tims_dict = {
        "TC1632": ["US31203", message, status]
    }
    print "US31203: Create a household"
    print "TC1632 :Create a household authorized for RestartTV only"
    try:
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
        # Initialize the Variables
        timeout = 2
        restart_service_config = []
        householdservicelist = None
        # set values based on config
        upm_host = cfg['upm']['host']
        upm_port = cfg['upm']['port']
        households_needed = cfg['basic_feature']['households_needed']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        region = cfg['region']
        cmdcRegion = cfg['cmdcRegion']
        adZone = cfg['adZone']
        marketingTarget = cfg['marketingTarget']
        restart_service_list = ["RESTART_ENABLER"]
        restart_service_list = json.dumps(restart_service_list)
        print "Restart Service List" + restart_service_list
        prefix = cfg['basic_feature']['household_prefix']
        throttle_milliseconds = cfg['basic_feature']['throttle_milliseconds']
        default_disk_quota = cfg['quotas']['diskQuota']
        default_tuner_quota = cfg['quotas']['numOfTuners']
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0, householdlimit - 1)
        householdid = prefix + str(index)
        deviceid = householdid + 'd'
        upm_headers = {
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Accept': 'application/json',
        }
        upm_headers1 = {
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Content-Type': 'application/json',
        }
        tuner_headers = {
            'Content-Type': 'text/plain',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Accept': 'text/plain',
        }

        hh_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }
        hh_create_payload = """{
          "householdId" : "%s",
          "householdStatus" : "ACTIVATED",
          "operateStatus": "ACTIVE",
          "locale" : {
               "region" : "%s",
               "cmdcRegion":"%s",
               "adZone": "%s",
               "marketingTarget": "%s"
                     },
          "devices": [   {
                "bssFullType": "cDVR_MANAGED",
                "operateStatus": "ACTIVE",
                "deviceId": "%s",
                "ipAddress": "10.1.1.15"
                }]
        }""" % (householdid, region, cmdcRegion, adZone, marketingTarget, deviceid)
    except:
        message = "Testcase Failed: Error occured in Configuration " + PrintException(True)
        delete_household(protocol, upm_port, householdid, upm_host)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1632"])
        return tims_dict

    try:
        print "###STEP1:Delete the household if it exists or create the Household if it does not exist with only Restart Service ###\n\n"
        create_hh = create_household(
            protocol, upm_port, householdid, upm_host, hh_headers, hh_create_payload)
        if create_hh:
            set_HouseholdEnabledServices_only(protocol,upm_host,upm_port,householdid,restart_service_list,upm_headers1,timeout)
            print "###STEP2:Fetch the the household Enabled Services ######\n\n"
            householdservicelist = get_HouseholdEnabledServices(
                protocol, upm_host, upm_port, householdid, upm_headers, timeout)
            print "Household Service List" + str(householdservicelist)
        else:
            message = "Testcase Failed: Unable to create the household"
            delete_household(protocol, upm_port, householdid, upm_host)
            print message
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC1632"])
            return tims_dict
        if householdservicelist:
            print "###STEP3:Verify that it has only Restart Service #####\n\n"
            list_compare = list_comp(
                restart_service_list, householdservicelist)
        else:
            message = "Testcase Failed: Unable to get the Enabled Services for the Household"
            delete_household(protocol, upm_port, householdid, upm_host)
            print message
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC1632"])
            return tims_dict
        if list_compare:
            print "Created Household has only Restart Service"
            print "###STEP4:Fetch the Diskquota  and Tuner quota of the household #######\n\n"
            disk_quota = fetch_full_details_diskquota(
                protocol, upm_host, upm_port, householdid, timeout, printflg)
            tuners_in_hh = get_numberoftuners(
                protocol, upm_host, upm_port, tuner_headers, householdid, timeout)
            disk_quota = json.loads(disk_quota.content)
            tuners_in_hh = int(tuners_in_hh)
        else:
            message = "Testcase Failed: HouseholdEnabledServices are not enabled completely as the list does not match with original enable service list "
            delete_household(protocol, upm_port, householdid, upm_host)
            print message
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC1632"])
            return tims_dict
        print "###STEP5:Verify that the default and fetched Tunerquota  and Diskquota are same ####\n\n"
        if (tuners_in_hh == default_tuner_quota) and (disk_quota == default_disk_quota):
            message = "Testcase Passed: Default Tunerquota,Diskquota and newly created household Tunerquota,Diskquota are same"
            delete_household(protocol, upm_port, householdid, upm_host)
            print message
            tims_dict = update_tims_data(tims_dict, 0, message, ["TC1632"])
            return tims_dict
        else:
            message = "Testcase Failed: Default Tunerquota,Diskquota and newly created household Tunerquota,Diskquota are not same"
            delete_household(protocol, upm_port, householdid, upm_host)
            print message
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC1632"])
            return tims_dict
    except:
        message = "Testcase Failed: Error occured in Script " + PrintException(True)
        delete_household(protocol, upm_port, householdid, upm_host)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1632"])
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
