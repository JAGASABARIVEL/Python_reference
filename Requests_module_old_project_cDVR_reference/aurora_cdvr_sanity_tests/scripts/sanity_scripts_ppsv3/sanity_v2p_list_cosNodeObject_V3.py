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
#   Get all cos node objects
##########################################################################


def doit(cfg, printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'  # rally initiatives
    US = 'Get all cos node objects'
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
    protocol = cfg['protocol']
    v2p_protocol = cfg['v2p']['protocol']
    channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
    channel_list.append(unicode(channel1))
    channel2 = cfg['test_channels']['GenericCh2']['ServiceId']
    channel_list.append(unicode(channel2))
    
    timeout = 2
    token = get_sm_api_token(cfg, timeout)
    if not token:
        TIMS_testlog.append(1)
        TIMS_testlog.append("Testcase Failed : Unable to get the sm api token")
        return TIMS_testlog
    Authorization = 'Bearer ' + token    
        
    
    pam_Node = cfg['v2p']['pam_node']
    port = cfg['v2p']['api_port']
    prefix = cfg['sanity']['household_prefix']
    headers = {
        'Authorization': Authorization
    }
    timeout = 2
    householdlimit = cfg['corner']['households_needed']
    index = random.randint(0, householdlimit - 1)
    check = 0
    message_list = []
    try:
        print "Getting  all cos node objects for: ", pam_Node
        householdid = prefix + str(index)
        url = v2p_protocol + "://" + pam_Node + \
            ":" + str(port) + "/v2/cosnodes"
        print "Get  all cos node objects via " + url
        r = sendURL("get", url, timeout, headers)
        if r is not None:
            if (r.status_code != 200):
                print "could not Get all cos node objects for pam_Node node: " + pam_Node
                print r.status_code
                print r.headers
                print r.content
                print "\nTestcase Failed: Get all cos node objects was not successful"
                TIMS_testlog.append(1)
                TIMS_testlog.append(
                    'Get all cos node objects was not successful.')
                return TIMS_testlog
            else:
                printLog("\nGet all cos node objects = " + r.content, printflg)
                responce = json.loads(r.content)
                for value in responce:
                    if value['properties']['adminState'] == 'inservice':
                        message = "Admin state is 'inservice' for id: " + \
                            value['id']
                        message_list.append(message)
                    else:
                        print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                        print "\nGet all cos node objects = " + r.content
                        print "\n" + "#" * 20 + " DEBUG ENDED " + "#" * 20 + "\n"
                        check = check + 1
                        message = "Admin state is not 'inservice' for id: " + \
                            value['id']
                        message_list.append(message)
        else:
            print "Error in getting responce, could not Get all cos node objects for pam_Node node: " + pam_Node
            TIMS_testlog.append(1)
            TIMS_testlog.append('Get all cos node objects was not successful.')
            return TIMS_testlog
        print "\n\n status for node objects: "
        for items in message_list:
            print items
        if check:
            print "\nTestcase failed: All id are not in 'inservice' state"
            TIMS_testlog.append(1)
            TIMS_testlog.append(
                'Get all cos node objects was not successful ' + message)
            return TIMS_testlog
        else:
            print "\nTestcase Passed: All id are in 'inservice' state"
            TIMS_testlog.append(0)
            TIMS_testlog.append(
                'Get all cos node objects was not successful ' + message)
            return TIMS_testlog
    except BaseException:
        message = "Error occured in script: " + PrintException(True)
        print message
        TIMS_testlog.append(1)
        TIMS_testlog.append(
            'Get all cos node objects was not successful ' + message)
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
