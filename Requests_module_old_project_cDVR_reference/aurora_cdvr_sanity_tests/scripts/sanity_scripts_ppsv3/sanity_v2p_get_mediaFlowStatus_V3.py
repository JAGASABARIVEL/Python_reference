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
#   Get Media workflow status
##########################################################################


def doit(cfg, printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'  # rally initiatives
    US = 'Get Media workflow status'
    TIMS_testlog = []
    TIMS_testlog = [name, I, US]

    # set values based on config
    protocol = cfg['protocol']
    v2p_protocol = cfg['v2p']['protocol']

    timeout = 2
    token = get_sm_api_token(cfg, timeout)
    if not token:
        TIMS_testlog.append(1)
        TIMS_testlog.append("Testcase Failed : Unable to get the sm api token")
        return TIMS_testlog
    Authorization = 'Bearer ' + token    
    
    
    v2p_masterNode = cfg['v2p']['masters']
    port = cfg['v2p']['mgmt_port']
    prefix = cfg['sanity']['household_prefix']
    headers = {
        'Authorization': Authorization
    }
    state_check = 0
    timeout = 2
    Worker_status = 0
    message_list = []
    for index, v2pmasternode in enumerate(v2p_masterNode):
        print "Getting  Media workflow status for: ", v2pmasternode
        householdid = prefix + str(index)
        url = v2p_protocol + "://" + v2pmasternode + ":" + \
            str(port) + "/sm/v2/type/mediaflowstatuses"
        print "Get  Media workflow status via " + url
        r = sendURL("get", url, timeout, headers)
        if r is not None:
            if (r.status_code != 200):
                message = "could not Get Media workflow status for v2p master node: " + v2pmasternode
                print message
                message_list.append(message)
                print r.status_code
                print r.headers
                print r.content
            else:
                printLog(
                    "\nGet Media workflow status = " +
                    r.content,
                    printflg)
                responce = json.loads(r.content)
                for value in responce:
                    if value['properties']['state'] == 'inservice':
                        pass
                    else:
                        print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                        print "\nGet Media workflow status = " + r.content
                        print "\n" + "#" * 20 + " DEBUG ENDED   " + "#" * 20 + "\n"
                        state_check = state_check + 1
                        message = "state for id: " + \
                            value['id'] + ": " + value['properties']['state'] + " v2p masternode: " + v2pmasternode
                        message_list.append(message)
                if state_check == 0:
                    Worker_status = Worker_status + 1
                    message = "All the state values are 'inservice' for: " + v2pmasternode
                    message_list.append(message)
        else:
            message = "could not Get Media workflow status for v2p master node: " + v2pmasternode
            message_list.append(message)
    for item in message_list:
        print item
    if Worker_status == len(v2p_masterNode):
        print "\n\nTestcase Passed: Get Media workflow status ran succesfully and all state are inservice"
        TIMS_testlog.append(0)
        TIMS_testlog.append('Get Media workflow status ran succesfully')
        return TIMS_testlog
    else:
        print "\n\nTestcase Failed: Get Media workflow status was not successful and all state are not inservice"
        TIMS_testlog.append(1)
        TIMS_testlog.append('Get Media workflow status was not successful.')
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
