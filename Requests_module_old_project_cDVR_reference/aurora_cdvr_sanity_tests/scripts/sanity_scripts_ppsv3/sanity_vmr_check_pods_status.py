#!/usr/bin/python

import os
import sys
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L3commonFunctions import *
##########################################################################
#   Check All Pods are in running state
##########################################################################


def doit(cfg, printflg=False):
    # announce
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'Check V2PC Application  Version'
    TIMS_testlog = [name, I, US]

    if not test_flag(cfg, "no_vmrv2p"):
        message = "Standalone VMR test cases. So Skipping it."
        print message
        TIMS_testlog.append(2)
        TIMS_testlog.append("Testcase Skipped : %s" % message)
        return TIMS_testlog

    failed_pods = []

    pods = get_vmr_pods()

    for k,v in pods.items():
        if v != 'running':
            failed_pods.append(k)

    if not failed_pods:
        print "\nTestcase Passed: All VMR pods are in running state"
        TIMS_testlog.append(0)
        TIMS_testlog.append('Check All VMR Pods are in running state')
        return TIMS_testlog
    else:
        print "\nTestcase Failed: Some VMR pods are not in running state"
        TIMS_testlog.append(1)
        TIMS_testlog.append('Check All VMR Pods are in running state')
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

