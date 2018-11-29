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
import math
from os.path import isfile
from genChannelLineup import *
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite

####################################################################################################################################################################################################
# TC1533: Confirm that when a new household is created, the Storage Quota assigned to it by default is the value that is stored in the Default Storage Quota field
# STEP1: Fetch Storage value of existing household (Global Value)
# STEP2: Create new household
# STEP3: Check the storage value for household created
# STEP4: Verify the two values are same
####################################################################################################################################################################################################
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
        "TC872": ["US31836", message, status]
    }
    print "TC872: Confirm that when a new household is created, the Storage Quota assigned to it by default is the value that is stored in the Default Storage Quota field"
    print "US31836: User case: As a SP, I want to be able to set a global storage quota value that will be assigned to all households upon their creation"
    try:
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
    
        #Initialize the Variables
        timeout = 2
        global_storagevalue = 0
        new_household_storagevalue = 0  
        # set values based on config
        adZone = cfg['adZone']
        marketingTarget = cfg['marketingTarget']
        enabledServices = '"{0}"'.format('", "'.join(cfg['enabledServices'])) 
        upm_host = cfg['upm']['host']
        pps_hosts = [cfg['pps']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        households_needed = cfg['basic_feature']['households_needed']
        cmdc_port = cfg['cmdc']['port']
        upm_port = cfg['upm']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        cmdcRegion = cfg['cmdcRegion']
        prefix = cfg['basic_feature']['household_prefix']
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        householdid_second = "GLOBAL" 
        hostlist = list(itertools.product(cmdc_hosts,pps_hosts))
    except:
        message = "Testcase Failed: Error Occured in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict,1, message, ["TC872"])
        return tims_dict

    for (cmdc_host,pps_host) in hostlist :
       try:
            print "Cleaning up the household bookings and recordings before testcase execution"
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            print "\n\n### STEP1: Fetch Storage value of existing household (Global Value) ###################################################################################################"
            global_storagevalue = fetch_full_details_diskquota(protocol,upm_host,upm_port,householdid,timeout,printflg=False) 
            if global_storagevalue:
                global_storagevalue = global_storagevalue.content
                print "Global storage value: ",global_storagevalue  
            else:
                message = "Testcase Failed: Unable to Fetch the Diskquota for the household"
                print message
                tims_dict = update_tims_data(tims_dict,1, message, ["TC872"])
                return tims_dict
    
            print "\n\n### STEP2: Create new household #########################################################################################################################################"
            result_household = create_ahousehold(protocol,upm_port,prefix,region,cmdcRegion,adZone,marketingTarget,householdid_second,enabledServices,upm_host)
            if result_household == True:
                print "Household created: ", householdid_second
            else:
                message = "Testcase Failed: Unable to create the household"
                print message
                tims_dict = update_tims_data(tims_dict,1, message, ["TC872"])
                return tims_dict

            print "\n\n### STEP3: Check the storage value for household created #################################################################################################################"
            new_household_storagevalue = fetch_full_details_diskquota(protocol,upm_host,upm_port,householdid_second,timeout,printflg=False)
            if new_household_storagevalue:
                new_household_storagevalue = new_household_storagevalue.content
                print "Storage value for new household: ", new_household_storagevalue   
            else:
                message = "Testcase Failed: Unable to Fetch the Diskquota for the household"
                print message
                tims_dict = update_tims_data(tims_dict,1, message, ["TC872"])
                return tims_dict

            print "\n\n### STEP4: Verify the two values (Global storage value & new household storage value) are same ############################################################################"
            if global_storagevalue == new_household_storagevalue:
                message = "Testcase Passed: New household was created with correct global value\n"
                delete_household(protocol,upm_port,householdid_second,upm_host)
                print message
                tims_dict = update_tims_data(tims_dict,0, message, ["TC872"])
                return tims_dict
            else:
                message = "Testcase Failed: New household was not created with correct global value"   
                delete_household(protocol,upm_port,householdid_second,upm_host)
                print message
                tims_dict = update_tims_data(tims_dict,1, message, ["TC872"])
                return tims_dict
       except:
          message = "Testcase Failed: Error Occured in Script " + PrintException(True)
          print message
          tims_dict = update_tims_data(tims_dict,1, message, ["TC872"])
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
    L = doit(cfg, True)
    exit(L)

