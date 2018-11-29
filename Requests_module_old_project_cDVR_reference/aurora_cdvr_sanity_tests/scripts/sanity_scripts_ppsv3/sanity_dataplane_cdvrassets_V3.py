#!/usr/bin/python

import os
import sys
import time
import requests
import json
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import get_sm_api_token
##########################################################################
#   Get cdvr assets
##########################################################################


def doit(cfg, printflg=False):
    disable_warning()  # Method Called to suppress all warnings
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'  # rally initiatives
    US = 'Get cdvr assets'
    TIMS_testlog = []
    TIMS_testlog = [name, I, US]

    print "Starting test " + test
    # set values based on config
    protocol = cfg['protocol']
    mos_url = cfg['mos']['v1url']
    msr_url = cfg['msr']['v1url']
    recording_api = cfg['recording_api']
    v2p_host = cfg['v2p']['masters']
    am_host = cfg['v2p']['assets_url']
    v2p_port = cfg['v2p']['interface_port']
    v2p_protocal = cfg['v2p']['protocol']
    headers = {'Accept': 'application/json;charset=utf-8'}
    
    timeout = 2
    token = get_sm_api_token(cfg, timeout)
    if not token:
        TIMS_testlog.append(1)
        TIMS_testlog.append("Testcase Failed : Unable to get the sm api token")
        return TIMS_testlog
    Authorization = 'Bearer ' + token
    headers['Authorization'] = Authorization    
    
    
    timeout = 5
    if recording_api == "v2p":
        asset = get_cdvr_asset(cfg)
        if asset:
            url = v2p_protocal + "://" + \
                am_host + ":" + str(v2p_port) + "/v1/assetworkflows/" + asset + "/assets"
            print "Get cdvr assets via ", url
        else:
            msg = 'Testcase failed :error in retrieving cdvr assets'
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog

    elif recording_api == "msr":
        url = msr_url + "/v1/assetworkflows/live/assets"
        print "Get cdvr assets via ", url
    else:
        url = mos_url + "/v1/assetworkflows/cdvr/assets"
        print "Get cdvr assets via ", url
    r = sendURL("get", url, timeout, headers)
    if r is not None:
        if (r.status_code != 200):
            print "Problem accessing: " + url
            print r.status_code
            print r.headers
            print r.content
            msg = 'Testcase failed :Could not access cdvr assets url.'
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog

        else:
            if r.content is None:
                print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                response = json.dumps(
                    json.loads(
                        r.content),
                    indent=4,
                    sort_keys=False)
                print "catalog response : \n\n"
                print response
                print "\n" + "#" * 20 + " DEBUG ENDED   " + "#" * 20 + "\n"
                msg = 'Testcase failed :error in retreiving the response for cdvr assets url.'
                print msg
                TIMS_testlog.append(1)
                TIMS_testlog.append(msg)
                return TIMS_testlog
            status_val = json.loads(r.content)
            status = json.dumps(
                json.loads(
                    r.content),
                indent=4,
                sort_keys=False)
            try:
                for val in status_val:
                    if val["status"]["state"] == "COMPLETE":
                        printLog(
                            "Asset capture is COMPLETE for contentId" +
                            val["contentId"],
                            printflg)
                        printLog(
                            "assetMgmtUrl  " +
                            val["assetMgmtUrl"],
                            printflg)
                    elif val["status"]["state"] == "PENDING":
                        printLog(
                            "Asset capture is scheduled to start in future" +
                            val["contentId"],
                            printflg)
                        printLog(
                            "assetMgmtUrl  " +
                            val["assetMgmtUrl"],
                            printflg)
                    elif val["status"]["state"] == "CAPTURING":
                        printLog(
                            "Asset capture state : " +
                            val["status"]["state"] +
                            " for contentId" +
                            val["contentId"],
                            printflg)
                        printLog(
                            "assetMgmtUrl  " +
                            val["assetMgmtUrl"],
                            printflg)
                    elif val["status"]["state"] == "FAILED":
                        printLog(
                            "Asset capture or publish failed due to " +
                            val["status"]["state"],
                            printflg)
                        printLog(val["status"]["reason"], printflg)
                    elif val["status"]["state"] == "DELETE_COMPLETE":
                        printLog(
                            "Asset delete completed for contentId" +
                            val["contentId"],
                            printflg)
                        printLog(
                            "assetMgmtUrl  " +
                            val["assetMgmtUrl"],
                            printflg)
                    elif val["status"]["state"] == "DELETE_FAILED":
                        printLog(
                            "Asset delete Failure for contentId" +
                            val["contentId"],
                            printflg)
                        printLog(
                            "assetMgmtUrl  " +
                            val["assetMgmtUrl"],
                            printflg)
                msg = 'Testcase passed :get cdvr assests ran successfuly.'
                print msg
                TIMS_testlog.append(0)
                TIMS_testlog.append(msg)
                return TIMS_testlog
            except BaseException:
                PrintException(True)
                msg = 'Testcase failed: Error occurred while retrieving cdvr assets'
                print msg
                TIMS_testlog.append(1)
                TIMS_testlog.append(msg)
                return TIMS_testlog
    msg = 'Testcase failed:could not get cdvr assets.'
    print msg
    TIMS_testlog.append(1)
    TIMS_testlog.append(msg)
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
