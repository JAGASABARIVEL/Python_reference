#!/usr/bin/python

import mypaths
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from V3_commonFunctions import *
import V3_planner as planner

print "Imported script 1 in V3 folder"

def doit(cfg, printflg=False):
    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        #updatevalue = updatetimsresultsjson(cfg ,start_time ,end_time ,rc ,'sanity-feature')
        # print updatevalue
        return rc
    except BaseException:
        print "Error Occurred in Script \n"
        PrintException()
        return (1)


def doit_wrapper(cfg, printflg=False):
    print "Imported script 1 in V3 folder in function doit."
    tims_list = ["TC", "DESC", "US", 1]
    return tims_list

if __name__ == "__main__":
    scriptName = os.path.basename(__file__)
    # read config file
    arguments = sys.argv
    cfg = relative_config_file(arguments, scriptName)
    if cfg['sanity']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
    L = doit_wrapper(cfg, True)
