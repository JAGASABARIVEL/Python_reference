#!/usr/bin/python

import os
import sys
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
##########################################################################
#   Get Asset workflows
##########################################################################


def doit(cfg, printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'  # rally initiatives
    US = 'Get Asset workflows'
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
    prefix = cfg['sanity']['household_prefix']
    channel_list = []
    asset_type = cfg['contentplayback']['url']
    asset_type = asset_type.strip('/')

    headers = {
        'Authorization': Authorization
    }
    state_check = 0
    timeout = 2
    Capture_status = 0
    message_list = []
    url_verify_string = ".m3u8"
    for index, v2pmasternode in enumerate(v2p_masterNode):
        print "Getting  Asset workflows for: ", v2pmasternode
        householdid = prefix + str(index)
        workflow_name_list = get_workflowname_list(
            v2p_protocol, v2pmasternode, port1, headers, asset_type, timeout)
        if workflow_name_list is None:
            print "Testcase Failed: Error in getting workflow_name_list"
            TIMS_testlog.append(1)
            TIMS_testlog.append('Get Asset workflows was not successful.')
            return TIMS_testlog
        else:
            url_state = 0
            for workflowname in workflow_name_list:
                url = v2p_protocol + "://" + v2pmasternode + ":" + \
                    str(port2) + "/v1/assetworkflows/" + workflowname
                print "Get  Asset workflows via " + url
                r = sendURL("get", url, timeout, headers)
                if r is not None:
                    if (r.status_code != 200):
                        message = "could not Get Asset workflows for workflowname: " + workflowname
                        print message
                        message_list.append(message)
                        print r.status_code
                        print r.headers
                        print r.content
                    else:
                        printLog(
                            "\nGet Asset workflows = " + r.content, printflg)
                        responce = json.loads(r.content)
                        template = responce['publishTemplates']
                        for val in template:
                            try:
                                if val['name'] == workflowname:
                                    variant = val['variants']
                                    for value in variant:
                                        if value['publishUrl']:
                                            publish_url = value['publishUrl']
                                            if publish_url.endswith(
                                                    url_verify_string):
                                                url_state = url_state + 1
                                                message = "Url for workflowname: " + \
                                                    workflowname + " : " + value['publishUrl']
                                                message_list.append(message)
                                            else:
                                                print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                                                print "\nGet Asset workflows = " + r.content
                                                print "\n" + "#" * 20 + " DEBUG ENDED   " + "#" * 20 + "\n"
                                                message = "Could not find url in desired format for: " + workflowname
                                                message_list.append(message)
                                        else:
                                            print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                                            printLog(
                                                "\nGet Asset workflows = " + r.content, printflg)
                                            print "\n" + "#" * 20 + " DEBUG ENDED   " + "#" * 20 + "\n"
                                            message = "Could not find url for workflowname: " + workflowname
                                            message_list.append(message)
                            except BaseException:
                                pass
            if url_state == len(workflow_name_list):
                message = "Fetched urls for all workflow names"
                message_list.append(message)
                Capture_status = Capture_status + 1
            else:
                message = "Testcase failed: could not Fetch urls for all workflow names"
                message_list.append(message)
    print "\n\nAsset workflow:  "
    for item in message_list:
        print item
    if Capture_status == len(v2p_masterNode):
        print "\n\nTestcase Passed: Get Asset workflows ran succesfully"
        TIMS_testlog.append(0)
        TIMS_testlog.append('Get Asset workflows ran succesfully')
        return TIMS_testlog
    else:
        print "\n\nTestcase Failed: Get Asset workflows was not successful "
        TIMS_testlog.append(1)
        TIMS_testlog.append('Get Asset workflows was not successful.')
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
