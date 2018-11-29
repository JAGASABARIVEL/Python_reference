#/usr/bin/python

import re
import time
import unicodedata
from collections import OrderedDict
from mockterminal import MockTerminal, summaryreport


class TestPing(MockTerminal):
    ping_concern = []

    def execute(self):
        try:
            self.setClassVariables()
            self.optionalCheck()
            self.result = self.run('ping localhost -c 1')
            self.parser()
            self.verify()
            self.status()
        except BaseException:
            print "Problem in running the ping test for this server."

    def setClassVariables(self):
        self.result = None
        self.parsedresult = OrderedDict()
        self.flag = []
        self.workaround = {
            "UNREACHABLE_REMOTE": {
                "report": "[WARNING] Sytem %s is not reachable.",
                "workaround": "[ACTION] Please check with system / network administrator for the reason of system %s being unreachable."},
            "REACHABLE_REMOTE": {
                "report": "[INFO] System %s is up and is reachable from remote machine.",
                "workaround": "[ACTION] No action required on the server %s."},
            "UNREACHABLE_LOCAL": {
                "report": "[WARNING] Sytem %s is not reachable locally.",
                "workaround": "[ACTION] Please check with system / network administrator for the reason of system %s being unreachable locally."},
            "REACHABLE_LOCAL": {
                "report": "[INFO] System %s is up and is reachable locally.",
                "workaround": "[ACTION] No action required on the server %s."}}

    def parser(self):

        mark = "SKIP"
        for values in self.result:
            if mark == "SKIP":
                if "ping statistics" in values:
                    mark = "STOP-1"
                else:
                    continue
            elif mark == "STOP-1":
                self.parsedresult.update({str(values.split()[
                                         6] + values.split()[7]).strip(','): str(values.split()[5].strip('%'))})
                break

    def optionalCheck(self):
        self.result = self.run(('ping %s -c 3' % (self.address)), local=True)
        if self.result == 0:
            pass  # self.flag.append("REACHABLE_REMOTE")
        else:
            self.flag.append("UNREACHABLE_REMOTE")

    def verify(self):
        if bool(int(self.parsedresult['packetloss'])) is False:
            pass  # self.flag.append("REACHABLE_LOCAL")
        else:
            self.flag.append("UNREACHABLE_LOCAL")

    def status(self):
        summaryreport[self.cache_key].append("PING REPORT")
        summaryreport[self.cache_key].append("\t ANALYSIS:")
        if not self.flag:
            summaryreport[self.cache_key].append(
                "[INFO] System's network is healthy and is reachable.")
        else:
            for flags in self.flag:
                summaryreport[self.cache_key].append(
                    self.workaround[flags]["report"] % (self.address))
            TestPing.ping_concern.append(True)
        summaryreport[self.cache_key].append("\t WORK-AROUND:")
        if not self.flag:
            summaryreport[self.cache_key].append(
                "[NO_ACTION] No actions items required.")
        else:
            for flags in self.flag:
                summaryreport[self.cache_key].append(
                    self.workaround[flags]["workaround"] % (self.address))
        summaryreport[self.cache_key].append("END REPORT")

    def tearDown(self):
        super(TestPing, self).close()
