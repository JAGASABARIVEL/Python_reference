#!/usr/bin/python

from collections import OrderedDict
import time
from pprint import pprint
import mypaths
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from V3_commonFunctions import *
import V3_planner as planner
from ChannelLineupV3 import ChannelLineupV3


class TestEventBooking(object):

    """
            Sanity test to check the user interactions like booking
            of an event and series are working as expected.
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
        self.ingest_minimum_delay = None
        self.timeslotinminutes = None
        self.channel = None
        self.events_data = None
        self.ingest_minimum_delay = None
        self.timeslotinminutes = None
        self.channel1 = None
        self.contentref = None
        self.starttime = None
        self.duration = None
        self.TC_PHASES.update({'1. COLLECTING CONFIGURATION': self.setConfig})
        self.TC_PHASES.update(
            {'2. CREATING AND PACKING MOCK INGEST OBJECT': self.ingestEvent})
        self.TC_PHASES.update(
            {'3. EVENT BOOKING PHASE': self.triggerEventBooking})
        self.kickTest()

    def getTims(self):
        return self.tims_list

    def kickTest(self):
        try:
            for phase in self.TC_PHASES:
                # time.sleep(5)
                print "=" * 30
                print phase
                print "=" * 30
                self.TC_PHASES[phase]()
            self.message = "Testcase Passed : Event booking is successfull and working as expected"
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
            print "4. CLEANUP PHASE"
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
        print "Starting test " + self.test

        print "US: As a SP, I want an API to perform an event booking"
        print "TC:Perform an event booking."

        # set values based on config
        self.protocol = self.cfg['protocol']
        self.prefix = self.cfg['sanity']['household_prefix']
        # Set a local variables
        self.timeout = 2
        plannerlimit = self.cfg['sanity']['households_needed']
        self.timeslotinminutes = self.cfg['test_channels']['mediumProgramLength']
        self.channel1 = self.cfg['test_channels']['GenericCh2']['ServiceId']
        plannerlimit = self.cfg['sanity']['households_needed']
        self.index_pool = range(0, plannerlimit - 1)
        self.ingest_minimum_delay = self.cfg['ci']['ingest_minimum_delay']
        self.timeslotinminutes = self.cfg['test_channels']['mediumProgramLength']

    def ingestObject(self):
        self.message = "Testcase Failed : Cannot create channellineup object."
        print "Creating an channellineup object..."
        self.ch = ChannelLineupV3()

    def getContentInfo(self):
        self.message = "Testcase failed : Error Occured while getting the contents from the planner."
        self.channel = self.channel1
        self.contentref = self.events_data[0][0]
        self.starttime = self.events_data[0][1]
        self.duration = self.events_data[0][2]

    def ingestEvent(self):
        self.ingestObject()
        self.message = 'Testcase Failed :  Cannot ingest contents into channellineup object.'
        self.events_data = self.ch.add_event(
            start_time_delay_mins=self.ingest_minimum_delay / 60,
            duration_min=self.timeslotinminutes,
            service_id=self.channel1,
            num_of_events=1)
        self.ch.write_xml()

    def triggerEventBooking(self):
        self.getContentInfo()
        for index in self.index_pool:
            self.plannerId = self.prefix + str(index)
            self.eventBooking()

    def triggerCleanPlanner(self):
        for index in self.index_pool:
            self.plannerId = self.prefix + str(index)
            self.cleanUp()

    def eventBooking(self):
        self.message = "Testcase failed : Error Occured while booking an event on the planner %s." % self.plannerId
        result, itemId_ev1 = create_booking(
            self.cfg, self.plannerId, self.channel, self.starttime, self.duration, self.contentref)
        assert result, self.message
        print "Suucessfully booked an event on the planner %s." % self.plannerId

    def cleanUp(self):
        print "[INFO] Clean up started for reverting the system to previous state..."
        planner.cleanup_planner(self.cfg, self.plannerId)

    def __del__(self):
        del self.ingestevent
        del self.TC_PHASES


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
    create = TestEventBooking(cfg, printflg=False)
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
