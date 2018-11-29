#!/usr/bin/python

import os
import sys
from pprint import pprint
import time
import requests
import json
import mypaths
from L1commonFunctions import *
from readYamlConfig import readYAMLConfigs


##########################################################################
#   Get cdvr services
##########################################################################

abspath = os.path.abspath(__file__)
scriptName = os.path.basename(__file__)
(test, ext) = os.path.splitext(scriptName)

def doit(cfg, printflg=False):
    print "Starting test " + test
    cdvrServices =  getCdvrServiceIds( cfg ) 
    if cdvrServices != None:
        if len(cdvrServices) > 0:
            if printflg:
                pprint(cdvrServices)
            return(0)
        else:
            print "No services with cdvrAvailable flag set"
    return(1)

def getCdvrServiceIds(cfg):
    serviceIdlist = []
    testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
    serviceIdlist.append(unicode(testchannel1))
    testchannel2 = cfg['test_channels']['GenericCh2']['ServiceId']
    serviceIdlist.append(unicode(testchannel2))
    return serviceIdlist


if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    #read config file 
    sa = sys.argv
    cfg = relative_config_file(sa,scriptName)
    if cfg['sanity']['print_cfg']:
         print "\nThe following configuration is being used:\n"
         pprint(cfg)
         print
    exit( doit(cfg, True) )

