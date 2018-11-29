#!/usr/bin/python

import os
import sys
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L3commonFunctions import get_sm_api_token

##########################################################################
#   Get  cos Node status
##########################################################################


def doit(cfg, printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'  # rally initiatives
    US = 'Get  cos Node status'
    TIMS_testlog = []
    TIMS_testlog = [name, I, US]
    if True:
        message = "Testcase warning :Skipping all COS PAM Node API because of authorization issue; Tosin is looking into it"
        print message
        TIMS_testlog.append(2)
        TIMS_testlog.append(message)
        return TIMS_testlog
    # set values based on config
    channel_list = []
    protocol = cfg['v2p']['protocol']
    channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
    channel_list.append(unicode(channel1))
    channel2 = cfg['test_channels']['GenericCh2']['ServiceId']
    channel_list.append(unicode(channel2))

    token = get_sm_api_token(cfg, timeout)
    if not token:
        TIMS_testlog.append(1)
        TIMS_testlog.append("Testcase Failed : Unable to get the sm api token")
        return TIMS_testlog
    Authorization = 'Bearer ' + token    
    
    pam_Node = cfg['v2p']['pam_node']
    if pam_Node is None:
        TIMS_testlog.append(1)
        TIMS_testlog.append('pam_Node not found')
        return TIMS_testlog
    port = cfg['v2p']['api_port']
    prefix = cfg['sanity']['household_prefix']
    headers = {
        'Authorization': Authorization
    }
    timeout = 2
    householdlimit = cfg['corner']['households_needed']
    index = random.randint(0, householdlimit - 1)
    check = 0
    try:
        print "Getting   cos Node status for: ", pam_Node
        householdid = prefix + str(index)
        url = protocol + "://" + pam_Node + ":" + \
            str(port) + "/v2/regions/region-0/nodestatuses"
        print "Get cos Node status via " + url
        r = sendURL("get", url, timeout, headers)
        if r is not None:
            if (r.status_code != 200):
                print "could not Get cos Node status for pam node: " + pam_Node
                print r.status_code
                print r.headers
                print r.content
                print "\nTestcase Failed: Get  cos Node status was not successful"
                TIMS_testlog.append(1)
                TIMS_testlog.append('Get  cos Node status was not successful.')
                return TIMS_testlog
            else:
                print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                print "\nGet  cos Node status = " + r.content
                print "\n" + "#" * 20 + " DEBUG ENDED " + "#" * 20 + "\n"
                responce = json.loads(r.content)
                for value in responce:
                    disk_status = []
                    status_list = []
                    inactive_state_check = 0
                    down_state_check = 0
                    warning = value['properties']['faultDetail']
                    name = value['name']
                    print "Name: ", name, "Warning: ", warning
                    for interface in value['properties']['interfaces']:
                        inter_name = interface['interface']
                        inter_status = interface['status']
                        status_list.append(inter_status)
                        print "Interface name: ", inter_name, "Interface Status: ", inter_status
                    if 'inactive' in status_list:
                        for statuslist in status_list:
                            if statuslist == 'inactive':
                                inactive_state_check = inactive_state_check + 1
                        if inactive_state_check == len(status_list):
                            message = "Testcase Failed: All the status are inactive for : " + name
                            print message
                            TIMS_testlog.append(1)
                            TIMS_testlog.append(message)
                            return TIMS_testlog
                        else:
                            print "All status values are not in active state for: ", name
                    else:
                        print "All the status are active for : ", name
                    disks = value['properties']['storage']['disks']
                    for disk in disks:
                        disk_name = disk['name']
                        disk_st = disk['status']
                        print "Disk name: ", disk_name, ", Disk status: ", disk_st
                        disk_status.append(disk_st)
                    if 'down' in disk_status:
                        for diskstatus in disk_status:
                            if diskstatus == 'down':
                                down_state_check = down_state_check + 1
                        if down_state_check == len(disk_status):
                            message = "Testcase Failed: All the status are 'down' for : " + name
                            print message
                            TIMS_testlog.append(1)
                            TIMS_testlog.append(message)
                            return TIMS_testlog
                        else:
                            print "\n\nAll status values aint in 'up' state for : ", name
                    else:
                        print "\n\nAll the status are up for : ", name
                    storage_used = value['properties']['usageStatus']['storageUsage']['used']
                    total_storage = value['properties']['usageStatus']['storageUsage']['total']
                    print "Storage used: ", storage_used, ", Total storage: ", total_storage
        else:
            print "could not Get cos Node status for v2p master node: " + v2pmasternode
            TIMS_testlog.append(1)
            TIMS_testlog.append('Get  cos Node status was not successful.')
            return TIMS_testlog

        print "\nTestcase Passed: Cos Node status were listed succesfully"
        TIMS_testlog.append(0)
        TIMS_testlog.append('Get cos Node status was not successful ')
        return TIMS_testlog
    except BaseException:
        message = "Error occured in script: " + PrintException(True)
        print message
        TIMS_testlog.append(1)
        TIMS_testlog.append(
            'Get cos Node status was not successful ' + message)
        return TIMS_testlog


if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    # read config file
    sa = sys.argv
    cfg = relative_config_file(sa, scriptName)
    if cfg['sanity']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
        print
    L = doit(cfg, True)
    exit(L[3])
