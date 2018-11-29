
#/usr/bin/python

import os
import sys
import re
import time
import json

import mypaths
from healthcheck.mockterminal import MockTerminal, summaryreport
from healthcheck.testping import TestPing
from healthcheck.testservice import TestService
from healthcheck.testdisk import TestDisk

from pprint import pprint
from L1commonFunctions import relative_config_file, PrintException, set_errorlogging
from L3commonFunctions import override_global_config_value

#from L2commonFunctions import *
#from L3commonFunctions import *

# TODO : Modify any static values in such a way to get it from configuration file.
# TODO : Make the suite to run in both cloud(aws) and in normal
# environment(chennai lab).


class TestPrecheck(object):
    """
    Description:
            This is a wrapper class which will invoke all the pre-check classes
            based on the incoming request from the entrypoint routine.
            The main purpose of the wrapper class is that,
                    - Abstraction of the core logic.
                    - Easy Readability for the maintainability.
                    - Loose Coupling
                    - Fine Controlling.

            bookSession()
                    This will try to create a separate session for each of the test.This can help us to execute the health-check in parallel in future.
                    If it can not establish a session with a specified server, the healthcheck will not be performed on that particular server.

            start()
                    This method will invoke all the execute() routine in all the instantiated classes.

            generateReport()
                    This method will provide the final formatted output to the console.

            tearDown()
                    This method will perform the teardown operation after the testcase(s) got completed.

    Usage:
            :server
            :username
            :password
            :server_type can be any of the following (SR/PPS/GOSRM)
    """
    print "\nStarting the system sanity health-check...\n"
    skippedserver = []
    anyconcern = []

    def __init__(
            self,
            server,
            username,
            sever_type,
            password=None,
            pemfile=None,
            cfg=None,
            aws=False):
        self.server = server
        self.test_ping = TestPing(
            server,
            username,
            password=password,
            sever_type=sever_type,
            pemfile=pemfile,
            cfg=cfg,
            aws=aws)
        self.test_service = TestService(
            server,
            username,
            password=password,
            sever_type=sever_type,
            pemfile=pemfile,
            cfg=cfg,
            aws=aws)
        self.test_disk = TestDisk(
            server,
            username,
            password=password,
            sever_type=sever_type,
            pemfile=pemfile,
            cfg=cfg,
            aws=aws)
        self.testname = None
        self.pingname = "Ping"
        self.servicename = "Service"
        self.diskname = "Disk"

    def bookSession(self):
        if self.test_ping.setConnection() or self.test_service.setConnection(
        ) or self.test_disk.setConnection() is False:
            summaryreport.update({self.server: [
                                 "\t Skipped since its connection timedout while trying to connect.\n"]})
            TestPrecheck.skippedserver.append(self.server)
            return False
        else:
            return True

    def _status(self, container=None, status="START"):
        column_length = 60
        inner_space = 4
        if container == None:
            print_string = "\t Status of %s Test" % (self.testname)
            if True in status:
                status = "ERROR"
            elif len(status) == 0:
                status = "OK"
            else:
                pass
            print_string_length = len(print_string)
            print print_string, ' '*(column_length - print_string_length - inner_space), "."*inner_space, " "*inner_space, "[%s]"% (status)
        else:
            print_string = "Health check on the server %s." % (container)
            print_string_length = len(print_string)
            #if status == "STARTED":print "\n"
            print print_string, ' '*(column_length - print_string_length), "."*10, "[%s]"% (status)
            #if status == "COMPLETED":print "\n"

    def start(self):

        self.testname = self.pingname
        self.test_ping.execute()
        self.ping_concern = self.test_ping.ping_concern
        self._status(status=self.ping_concern)

        self.testname = self.servicename
        self.test_service.execute()
        self.service_concern = self.test_service.service_concern
        self._status(status=self.service_concern)

        self.testname = self.diskname
        self.test_disk.execute()
        self.disk_concern = self.test_disk.disk_concern
        self._status(status=self.disk_concern)

        if isinstance(self.ping_concern, list):TestPrecheck.anyconcern.extend(self.ping_concern)
        if isinstance(self.service_concern, list):TestPrecheck.anyconcern.extend(self.service_concern)
        if isinstance(self.disk_concern, list):TestPrecheck.anyconcern.extend(self.disk_concern)
        #print "TestPrecheck.anyconcern :", TestPrecheck.anyconcern, type(TestPrecheck.anyconcern)

    def generateReport(self):
        if TestPrecheck.skippedserver:
            print "\n" * 2, "\t" * 4, " SKIPPED SERVERS ", "\n" * 2
            for server in TestPrecheck.skippedserver:
                print " \t" * 4, "-", server
            print "\n"

        print "\n" * 2, "\t" * 4, " HEALTH-CHECK SUMMARY ", "\n" * 2
        for server in summaryreport.keys():
            print "\t", "=" * 22, "\n", "\t", "SERVER: %s" % (server), "\n", "\t", "=" * 22
            for content in summaryreport[server]:
                if content.endswith(
                        "REPORT") and not content.startswith("END"):
                    print "\n", "\t" * 2, "*" * 56
                    print "\t" * 2, "*", "" * 4, "\t" * 2, " %s " % (content), "" * 4, "\t" * 3, "*"
                    print "\t" * 2, "*" * 56
                elif content.endswith(":"):
                    print "\t", content
                elif content.startswith("END"):
                    print "\t" * 2, "*" * 15, "\t" * 2, " %s " % (content), "\t" * 2, "*" * 15, "\n"
                else:
                    print "\t" * 3, content

    def tearDown(self):
        self.test_ping.tearDown()
        self.test_service.tearDown()
        self.test_disk.tearDown()

    def returnTims(self):
        # self.service_concern
        if True in TestPrecheck.anyconcern:
            message = "The servers/instances are in bad health to run the testsuite.Please refer the healthcheck output for more information."
            self.tims_list = ["TC", "DESC", "US", 1, message]
            return self.tims_list
        else:
            message = "All the servers/instances are at good health to run the testsuite..."
            self.tims_list = ["TC", "DESC", "US", 0, message]
            return self.tims_list


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
        message = "Error Occurred in Script \n"
        print message
        PrintException()
        return ["TC", "DESC", "US", 1, message]


def querryConsul(cfg):
    print "Inside querryConsul"
    cmd = "curl %s:%s%s" % (cfg["consul"]["host"],
                            cfg["consul"]["port"],
                            cfg["consul"]["running_instances_collection_api"])
    if "username" in cfg["consul"].keys():
        terminal = MockTerminal(cfg["consul"]["username"], "127.0.0.1")
    else:
        terminal = MockTerminal(cfg["username"], "127.0.0.1")
    consulresponse = terminal.run(cmd, local=True, statusonly=False)
    return consulresponse


def doit_wrapper(cfg, printflg=False):

    test = None
    nodes_to_be_checked = cfg["health-check"]["nodes"]
    serverset = {}

    """
        Description:
                This is the entrypoint of the pre-check which will instantiate the
                wrapper class for the "TestPrecheck" with a separate object
                for every available server(for which the pre-check to be performed).
        Usage:
                :server
                :username
                :password
                :server_type can be any of the following (SR/PPS/GOSRM)
        """

    if "host" in cfg["consul"].keys():
        consulresponse = querryConsul(cfg=cfg)
        data = json.loads(consulresponse)
        for service in data:
            for nodes in nodes_to_be_checked:
                if cfg[nodes]["consul_search_string"] in service["Node"]:
                    if 'username' in cfg[nodes].keys():
                        serverset.update(
                            {
                                service["Address"] +
                                "-" +
                                nodes: {
                                    'username': cfg[nodes]["username"],
                                    'address': service["Address"],
                                    'servertype': nodes}})
                    else:
                        serverset.update(
                            {
                                service["Address"] +
                                "-" +
                                nodes: {
                                    'username': cfg["username"],
                                    'address': service["Address"],
                                    'servertype': nodes}})

        for server in serverset.keys():
            #test = TestPrecheck(server, serverset[server]['username'], sever_type=serverset[server]['sever_type'], pemfile=serverset[server]['pemfile'], aws=True, cfg=cfg)
            test = TestPrecheck(
                serverset[server]["address"],
                serverset[server]['username'],
                sever_type=serverset[server]["servertype"],
                aws=True,
                cfg=cfg)
            test._status(container = server, status="START")
            if test.bookSession():
                test.start()
                test.tearDown()
            test._status(container = server, status="DONE")

    else:
        # TODO:Load the values from configuration file.
        for nodes in nodes_to_be_checked:
            if 'username' in cfg[nodes].keys():
                serverset.update(
                    {
                        cfg[nodes]["host"] +
                        "-" +
                        nodes: {
                            'username': cfg[nodes]["username"],
                            'address': cfg[nodes]["host"],
                            'servertype': nodes}})
            else:
                serverset.update(
                    {
                        cfg[nodes]["host"] +
                        "-" +
                        nodes: {
                            'username': cfg["username"],
                            'address': cfg[nodes]["host"],
                            'servertype': nodes}})

        for server in serverset.keys():
            #test = TestPrecheck(server, serverset[server]['username'], sever_type=serverset[server]['sever_type'], password=serverset[server]['password'], cfg=cfg)
            test = TestPrecheck(
                serverset[server]["address"],
                serverset[server]['username'],
                sever_type=serverset[server]["servertype"],
                cfg=cfg)
            test._status(container = server, status="START")
            if test.bookSession():
                test.start()
                test.tearDown()

            test._status(container = server, status="DONE")

    print "Health Check completed successfully.Below is the summary of the health-check.", "\n" * 2
    test.generateReport()
    return test.returnTims()


if __name__ == "__main__":
    scriptName = os.path.basename(__file__)
    # read config file
    arguments = sys.argv
    cfg = relative_config_file(arguments, scriptName)
    if cfg['sanity']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
    L = doit(cfg, True)
