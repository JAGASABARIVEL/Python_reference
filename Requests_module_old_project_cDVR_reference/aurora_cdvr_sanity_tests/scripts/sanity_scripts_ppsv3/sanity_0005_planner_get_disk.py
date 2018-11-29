#!/usr/bin/python

from collections import OrderedDict
from pprint import pprint
import mypaths
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from V3_commonFunctions import *
import V3_planner as planner


class TestAuthzDisk():

    """
            Sanity test to check whether authz supplemet such as
                    1. diskquota,
            for a planner could be retrived successfully.
    """

    TC_PHASES = OrderedDict()

    def __init__(self, cfg, printflg=False):
        self.message = None
        self.status = None
        self.tims_list = []
        self.protocol = None
        self.cfg = cfg
        self.timeout = None
        self.plannerId = None
        self.TC_PHASES.update({'1. COLLECTING CONFIGURATION': self.setConfig})
        self.TC_PHASES.update(
            {'2. GETTING DISK QUOTA DETAILS FROM ALL THE PLANNERS': self.triggerGetDiskQuota})
        self.kickTest()

    def getTims(self):
        return self.tims_list

    def kickTest(self):
        try:
            for phase in self.TC_PHASES:
                print "=" * 30
                print phase
                print "=" * 30
                self.TC_PHASES[phase]()
            self.message = "Testcase Passed : Successfully able to collect the diskquota details from all the planner(s) allocated for the TCs."
            self.tims_list.append(0)
            self.tims_list.append(self.message)
        except Exception as e:
            self.message = "Testcase Failed: " + str(e)
            self.tims_list.append(1)
            self.tims_list.append(self.message)
        except AssertionError as ae:
            self.message = "Testcase Failed:" + str(ae)
            self.tims_list.append(1)
            self.tims_list.append(self.message)
        finally:
            print "=" * 30
            print "3. CLEANUP PHASE"
            print "=" * 30
            self.triggerCleanPlanner()
            print self.message

    def setConfig(self):
        self.message = "Testcase failed : Error Occured while configuration collection "
        self.status = 3
        self.tims_list = ["TC", "DESC", "US"]

        self.abspath = os.path.abspath(__file__)
        self.scriptName = os.path.basename(__file__)
        (self.test, self.ext) = os.path.splitext(self.scriptName)
        print "US: As a SP, I want an API to fetch the diskquota details from the planner."
        print "TC: Check whether we are able to fetch the information about the diskquota details from the created planner."

        # set values based on config
        self.protocol = self.cfg['protocol']
        self.prefix = self.cfg['sanity']['household_prefix']
        # Set a local variables
        self.timeout = 2
        plannerlimit = self.cfg['sanity']['households_needed']
        self.index_pool = range(0, plannerlimit - 1)

    def triggerGetDiskQuota(self):
        for index in self.index_pool:
            self.plannerId = self.prefix + str(index)
            self.getDiskQuota()

    def triggerCleanPlanner(self):
        for index in self.index_pool:
            self.plannerId = self.prefix + str(index)
            self.cleanUp()

    def getDiskQuota(self):
        self.message = "Testcase Failed : Cannot able to collect the diskquota details from the planner."
        response = planner.get_planner_diskquota(self.cfg, self.plannerId)
        assert response, self.message
        print "[INFO] Successfully able to get the diskquota from the planner %s.\nDisk Quota : %s.\n" % (self.plannerId, response)

    def cleanUp(self):
        print "[INFO] Clean up started for reverting the system to previous state..."
        planner.cleanup_planner(self.cfg, self.plannerId)


def doit(cfg, printflg=False):
    try:
        start_time = time.time()
        set_errorlogging()
        rc = doit_wrapper(cfg, printflg)
        end_time = time.time()
        return rc
    except BaseException:
        print "Error Occurred in Script \n"
        PrintException()
        return (1)


def doit_wrapper(cfg, printflg=False):
    create = TestAuthzDisk(cfg, printflg=False)
    return create.getTims()


if __name__ == "__main__":
    scriptName = os.path.basename(__file__)
    # read config file
    arguments = sys.argv
    cfg = relative_config_file(arguments, scriptName)
    if cfg['sanity']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
    doit(cfg, True)
