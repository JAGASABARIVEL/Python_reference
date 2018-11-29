#!/usr/bin/python

import os
import sys
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
##########################################################################
#   Get Channel Capture status
##########################################################################


def doit(cfg, printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'  # rally initiatives
    US = 'Get Channel Capture status'
    TIMS_testlog = []
    TIMS_testlog = [name, I, US]

    # set values based on config
    protocol = cfg['protocol']
    v2p_protocol = cfg['v2p']['protocol']
    token = cfg['v2p']['api_token']
    Authorization = 'Bearer cisco:' + token
    v2p_masterNode = cfg['v2p']['masters']
    port1 = cfg['v2p']['api_port']
    port2 = cfg['v2p']['interface_port']
    asset_type = cfg['contentplayback']['url']
    asset_type = asset_type.strip('/')
    prefix = cfg['sanity']['household_prefix']
    channel_list = []
    headers = {
        'Authorization': Authorization
    }
    state_check = 0
    timeout = 2
    Capture_status_check = 0
    message_list = []

    for index, v2pmasternode in enumerate(v2p_masterNode):
        channel_list = get_v2p_contentID(
            v2p_protocol,
            v2pmasternode,
            port1,
            headers,
            timeout,
            printflg)
        if channel_list:
            print "service list :", channel_list
        else:
            TIMS_testlog.append(1)
            TIMS_testlog.append('unable to retrived the channel list')
            return TIMS_testlog
        print "Getting  Channel Capture status for: ", v2pmasternode
        householdid = prefix + str(index)
        workflow_name_list = get_workflowname_list(
            v2p_protocol, v2pmasternode, port1, headers, asset_type, timeout)
        if workflow_name_list is None:
            print "Testcase Failed: Error in getting workflow_name_list"
            TIMS_testlog.append(1)
            TIMS_testlog.append(
                'Get Channel Capture status was not successful.')
            return TIMS_testlog
        else:
            workflow_status_check = 0
            print workflow_name_list
            for workflowname in workflow_name_list:
                url = v2p_protocol + "://" + v2pmasternode + ":" + \
                    str(port2) + "/v1/assetworkflows/" + workflowname + "/assets"
                print "Get Channel Capture status via " + url
                r = sendURL("get", url, timeout, headers)
                if r is not None:
                    if (r.status_code != 200):
                        message = "could not Get Channel Capture status for v2p master node: " + \
                            v2pmasternode + "for workflowname :" + workflowname
                        print message
                        message_list.append(message)
                        print r.status_code
                        print r.headers
                        print r.content
                    else:
                        printLog(
                            "\nGet Channel Capture status = " +
                            r.content,
                            printflg)
                        responce = json.loads(r.content)
                        channel_status = 0
                        for value in responce:
                            if value['contentId'] in channel_list:
                                Capture_Status = value['status']['captureStatus']
                                for status in Capture_Status:
                                    if status['state'] == 'CAPTURING':
                                        channel_status = channel_status + 1
                                        message = "workflow name: " + workflowname + \
                                            " is in CAPTURING state" + "for channel Id : " + value['contentId']
                                        message_list.append(message)
                                    else:
                                        print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                                        print "\nGet Channel Capture status = " + r.content
                                        print "\n" + "#" * 20 + " DEBUG ENDED   " + "#" * 20 + "\n"
                                        message = "workflow name: " + workflowname + \
                                            " is not in CAPTURING state" + "for channel Id : " + value['contentId']
                                        message_list.append(message)
                        if channel_status != len(channel_list):
                            message = "Could not verify CAPTURING state for workflowname: " + workflowname
                            message_list.append(message)
                        else:
                            workflow_status_check = workflow_status_check + 1
                            message = "CAPTURING state verified for workflowname: " + workflowname
                            message_list.append(message)
                else:
                    message = "Error in retrieving response for workflowname : : " + workflowname
                    message_list.append(message)
            if workflow_status_check == len(workflow_name_list):
                Capture_status_check = Capture_status_check + 1

    print "\n\nCapture status: "
    for item in message_list:
        print item
    if Capture_status_check == len(v2p_masterNode):
        print "\n\nTestcase Passed: Get Channel Capture status ran succesfully and all state are inservice"
        TIMS_testlog.append(0)
        TIMS_testlog.append('Get Channel Capture status ran succesfully')
        return TIMS_testlog
    else:
        print "\n\nTestcase Failed: Get Channel Capture status was not successful and all state are not inservice"
        TIMS_testlog.append(1)
        TIMS_testlog.append('Get Channel Capture status was not successful.')
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
