#!/usr/bin/python


import json
import os
import sys
from pprint import pprint
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite

#######################################################################################
#Test Steps :Create a household authorized for CatchupTV only.
# STEP1: Get the default values from config files
# STEP2: Trigger a create house hold to UPM
# STEP3: fetch the services enabled and default values
# STEP4: Verify house hold has the default values
# STEP5: Update the house hold for CATCH_ENABLER Alone
# STEP6: Verify house hold has only CATCH_ENABLER service
#######################################################################################
def doit(cfg,printflg=False):
    try :
        start_time = time.time()
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

def doit_wrapper(cfg, printflg=True):
    message = ""
    status = 3
    tims_dict = {
       "TC1631": ["US31203", message, status]
        }
    print "\n US31203: Create a household"
    print "\nTC1631: Create a household authorized for CATCHUP Service"

    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test

    # set values based on config
    try:
        print "##STEP1 Fetching the default values ###\n"
        protocol = cfg['protocol']
        port = cfg['upm']['port']
        prefix = cfg['basic_feature']['household_prefix']
        region = cfg['region']
        cmdcRegion = cfg['cmdcRegion']
        adZone = cfg['adZone']
        marketingTarget = cfg['marketingTarget']
        prefix = cfg['basic_feature']['household_prefix']
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0, householdlimit - 1)
        householdid = prefix + str(index)
        print "Household name which is used for creating" + householdid
        host = cfg['upm']['host']
        def_disk_value = cfg['quotas']['diskQuota']
        def_tuners = cfg['quotas']['numOfTuners']

        headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Accept': 'application/json'	
        }
        deviceid = householdid + 'd'
        payload = """
        {
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
                    "ipAddress": "10.2.1.15"
                    }]
        }
        """ % (householdid, region, cmdcRegion, adZone, marketingTarget, deviceid)
    except:
        message = "TestCase Failed : Error Occurred in Configuration " + PrintException(True)
        print message
        tims_dict = update_tims_data(tims_dict,1,message,["TC1631"])
        return tims_dict

    #print payload
    try:
        print("Deleting the existing householdid")
        delete_household(protocol,port,householdid,host)
    except:
        message="TestCase Failed : Exception in deleting the household"
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1631"])
        return tims_dict

    url = protocol + "://" + host + ":" + str(port) + "/upm/households/" + householdid

    # Sending Request to create house hold
    try:
        print "Create Household URL : " + str(url)
        print "##STEP2: Create a house hold in UPM###\n "
        r = requests.put(url, data=payload, headers=headers, timeout=10)
        if r.status_code == 201:
            get_value= requests.get(url,headers=headers, timeout=10)
            print "Content Response:\n", str(get_value.content)
            resp_value=json.loads(get_value.content)
            # Fetching the values from response
            print "##STEP3 Fetching the default values\n"
            service_value =  resp_value["enabledServices"]
            print "Enabled Services value from response: ", service_value
            disk_value = resp_value["diskQuota"]
            tunner_value = resp_value["numOfTuners"]
            print "Disk Quota value from response: ", disk_value
            print "Tuner Value from response: ", tunner_value
            print "Length of service: ", len(service_value)
            #Verifying the values with default Configuration
            print "##STEP4 Verifying againt default values\n"
            if len(service_value) == 2 and "CDVR" in service_value and "ALLOW-CDVR-TIME-BASED-RECORDING" in service_value:
                print "House hold contains cDVR services"
                if disk_value == def_disk_value:
                    print "House hold has default disk value"
                    if tunner_value == def_tuners:
                        print "House hold has default tunner value"
                    else:
                        message = "TestCase Failed : House hold has doesnt have default tunner value"
                        delete_household(protocol, port, householdid, host)
                        print message
                        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1631"])
                        return tims_dict
                else:
                    message = "TestCase Failed : House hold has doesnt have default disk value"
                    delete_household(protocol, port, householdid, host)
                    print message
                    tims_dict = update_tims_data(tims_dict, 1, message, ["TC1631"])
                    return tims_dict
            else:
                message = "TestCase Failed : House hold has doesnt have default services"
                delete_household(protocol, port, householdid, host)
                print message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC1631"])
                return tims_dict
        else:
            message="TestCase Failed : Response code is other than 201"
            delete_household(protocol,port,householdid,host)
            print "Status Code: ",r.status_code
            print message
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC1631"])
            return tims_dict
    except:
        message = "TestCase Failed : Request is not being sent to UPM"
        delete_household(protocol,port,householdid,host)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1631"])
        return tims_dict
    print "##STEP5 Update HouseHold with only CATCHUP_ENABLER service \n"
    try:
        service_list=["CATCHUP_ENABLER"]
        print "Service list: ", service_list
        url_enable = protocol + "://" + host + ":" + str(port) + "/upm/households/" + householdid + "/enabledServices"
        r1 = requests.put(url_enable, data=json.dumps(service_list), headers=headers, timeout=10)
        if r1.status_code == 200:
            get_value_after_enable_service = requests.get(url, headers=headers, timeout=10)
            resp_value_after_enable_service = json.loads(get_value_after_enable_service.content)
            service_value_after_enable_service = resp_value_after_enable_service["enabledServices"]
            print "Enabled Services value from response: ", service_value_after_enable_service
            print "Length of service: ", len(service_value_after_enable_service)
            print "##STEP6 Verify House Hold has  CATCHUP_ENABLER service \n"
            if len(service_value_after_enable_service) == 1 and "CATCHUP_ENABLER" in service_value_after_enable_service:
                message = "TestCase Passed : Only CATCHUP_ENABLER service has been enabled for House Hold"
                delete_household(protocol, port, householdid, host)
                print message
                tims_dict = update_tims_data(tims_dict, 0, message, ["TC1631"])
                return tims_dict
            else:
                message = "TestCase Failed : CATCHUP_ENABLER service is not been enabled for House Hold"
                delete_household(protocol, port, householdid, host)
                print message
                tims_dict = update_tims_data(tims_dict, 1, message, ["TC1631"])
                return tims_dict
        else:
            message = "TestCase Failed : set_HouseholdEnabledService returned fail"
            delete_household(protocol, port, householdid, host)
            print message
            tims_dict = update_tims_data(tims_dict, 1, message, ["TC1631"])
            return tims_dict
    except:
        message = "TestCase Failed : Error Occurred in Script " + PrintException(True)
        delete_household(protocol, port, householdid, host)
        print message
        tims_dict = update_tims_data(tims_dict, 1, message, ["TC1631"])
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

