#!/usr/bin/python
import json
import os
import sys
from pprint import pprint
import calendar
import random
import time
import itertools
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *

##########################################################################
#   Get Copy Type of an Event V3
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
        US = 'get CopyType - V3'
        TIMS_testlog = []
        TIMS_testlog = [name, I, US]
        print "Starting test " + test

        timeout = 2
        result = "FAIL"
        try:
            """
                Code to GET metdataContentRef, start time, end time, from S3 Sftp here
            """
            random_contentId = "metdataContentRef"
            startTime = "take it from s3 sftp"
            endTime = "take it from s3 sftp"
            scheduleid = "eventRef"
            serviceEqKey = "sek"

            print "### Passing StartTime, EndTime, ServiceEquivalenceKey, ID to iPOM for finding CopyType of the " \
                  "event #### \n"
            copyType_resp = get_copyType(
                cfg, scheduleid, serviceEqKey, startTime, endTime, timeout=2)
            print "copytype", copyType_resp
            resp = json.loads(copyType_resp.content)
            event_copyType = resp[0]['policy']['copyType']
            print "CopyType of the event with contentID %s is" % scheduleid, event_copyType
            assert event_copyType is not None, "Testcase Failed: copyType is empty"
            msg = "Testcase Passed: CopyType is found for contentID"
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
