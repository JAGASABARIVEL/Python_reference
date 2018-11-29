#!/usr/bin/python

import os
import sys
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
##########################################################################
#   Get service api
##########################################################################


def doit(cfg, printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'  # rally initiatives
    US = 'Get service api'
    TIMS_testlog = []
    TIMS_testlog = [name, I, US]

    # set values based on config
    protocol = cfg['protocol']
    v2p_protocol = cfg['v2p']['protocol']
    token = cfg['v2p']['api_token']
    Authorization = 'Bearer cisco:' + token
    v2p_masterNode = cfg['v2p']['masters']
    port = cfg['v2p']['api_port']
    prefix = cfg['sanity']['household_prefix']
    headers = {
        'Authorization': Authorization
    }
    timeout = 5
    message_list = []
    verify_check = 0
    for index, v2pmasternode in enumerate(v2p_masterNode):
        print "Getting  service api for: ", v2pmasternode
        householdid = prefix + str(index)
        url = v2p_protocol + "://" + v2pmasternode + ":" + \
            str(port) + "/v2/regions/region-0/serviceapis"
        print "Get  service api via " + url
        r = sendURL("get", url, timeout, headers)
        if r is not None:
            if (r.status_code != 200):
                message = "could not Get service api for v2p master node: " + v2pmasternode
                message_list.append(message)
                print r.status_code
                print r.headers
                print r.content
            else:
                if r.content is None:
                    print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                    print "\nGet service api = " + r.content
                    print "\n" + "#" * 20 + " DEBUG ENDED   " + "#" * 20 + "\n"
                else:
                    printLog("\nGet service api = " + r.content, printflg)
                    message = "Got the service api succesfully for v2pnode: " + v2pmasternode
                    message_list.append(message)
                    verify_check = verify_check + 1
        else:
            message = "could not Get service api for v2p master node: " + v2pmasternode
            message_list.append(message)
    print "\n\nget service api results: "
    for item in message_list:
        print item
    if verify_check == len(v2p_masterNode):
        print "\nTestcase Passed: Get service api ran succesfully"
        TIMS_testlog.append(0)
        TIMS_testlog.append('Get service api ran succesfully')
        return TIMS_testlog
    else:
        print "\nTestcase Failed: Get service api was not successful"
        TIMS_testlog.append(1)
        TIMS_testlog.append('Get service api was not successful.')
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
