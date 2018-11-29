#!/usr/bin/python
import json
import os
import sys
from pprint import pprint
import calendar
import requests
import random
import time
import itertools
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *

##########################################################################
#   Get event policies by window
##########################################################################


def doit(cfg, printflg=False):
    try:
        disable_warning()  # Method Called to suppress all warnings
        any_host_pass = 0
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        name = (__file__.split('/'))[-1]
        I = 'Core DVR Functionality'  # rally initiatives
        US = 'Pps Booking'
        TIMS_testlog = []
        TIMS_testlog = [name, I, US]
        print "Starting test " + test
        index = 0
        cmdc_hosts = get_hosts_by_config_type(cfg, 'cmdc', printflg)
        pps_hosts = get_hosts_by_config_type(cfg, 'pps', printflg)
        if cmdc_hosts is None or pps_hosts is None:
            msg = 'Testcase failed : unable to get host ip '
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        prefix = cfg['sanity']['household_prefix']
        throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
        if throttle_milliseconds < 1:
            throttle_milliseconds = 25
        timeout = 2
        result = "FAIL"
        hosts_list = list(itertools.product(cmdc_hosts, pps_hosts))
        printLog("Final list :" + str(hosts_list), printflg)
        for (cmdc_host, pps_host) in hosts_list:
            if (len(cmdc_host) > 1 and len(pps_host) > 1):
                time.sleep(throttle_milliseconds / 1000.0)
            try:
                print "### Send out the request to IPOM for getEventPolicy"
                response_eventPolicy = get_eventPolicy(cfg, timeout=2)
                assert response_eventPolicy, "Test case Failed: getEventPolicy response is empty"
                msg = "Testcase Passed: getEventPolicy response has contents"
                TIMS_testlog.append(0)

            except AssertionError as ae:
                msg = str(ae)
                TIMS_testlog.append(1)

            except Exception as e:
                msg = str(e)
                TIMS_testlog.append(1)
            finally:
                print msg
                TIMS_testlog.append(msg)
                return TIMS_testlog

    except BaseException:
        msg = "Testcase failed : Error Occurred in Script: " + \
            PrintException(True)
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
