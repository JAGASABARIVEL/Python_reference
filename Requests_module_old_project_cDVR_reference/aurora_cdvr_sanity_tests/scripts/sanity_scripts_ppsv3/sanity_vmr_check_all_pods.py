#!/usr/bin/python

import os
import sys
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L3commonFunctions import *
##########################################################################
#   Check All Pods are present as part of VMR
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

    # Mandatory pods for VMR
    vmr_components = ('a8-updater', 'archive-agent', 'api', 'bmw', 'dash-origin', 'health-agent',
                      'health-monitor', 'manifest-agent', 'nsa', 'reconstitution-agent',
                      'recorder-manager', 'sats-server', 'segment-recorder', 'ui', 'zookeeper')

    di = get_vmr_pods()

    pod_count = 0
    for pod in vmr_components:
        print 'checking {0:<20}'.format(pod),
        for val in di.keys():
            if pod in val:
                print ' - present'
                pod_count += 1
                break
        else:
            print " - Not present"

    if pod_count == len(vmr_components):
        print "\nTestcase Passed: All VMR pods are present"
        TIMS_testlog.append(0)
        TIMS_testlog.append('Check All VMR Pods are present')
        return TIMS_testlog
    else:
        print "\nTestcase Failed: All VMR pods are not present"
        TIMS_testlog.append(1)
        TIMS_testlog.append('Check All VMR Pods are present')
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

