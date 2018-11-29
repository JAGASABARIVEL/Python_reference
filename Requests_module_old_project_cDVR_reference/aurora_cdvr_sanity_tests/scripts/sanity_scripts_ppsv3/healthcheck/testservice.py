#/usr/bin/python

import re
import time
import unicodedata
from ast import literal_eval as eval
import mypaths
from mockterminal import MockTerminal, summaryreport
from L3commonFunctions import override_global_config_value

class TestService(MockTerminal):
    """
    """
    service_concern = []
    max_reties = 0

    def execute(self):
        try:
            if TestService.max_reties == 0:
                self.setClassVariables()
                self.setServer()
            for service in self.services:
                service = self.services[service]
                # This falg is the one which controls whether the service has to be restarted if it found to be dead.
                self.skipworkaround = override_global_config_value(self.cfg, self.sever_type, "service_restart")
                #self.cfg[self.sever_type]["service_restart"]
                self.response = self.run(
                    '%s %s status' %
                    (self.setsudoservice, service), sudo=self.sudo)
                if self.result:
                    self.result.update({service: self.response})
                else:
                    self.result = {service: self.response}
                # time.sleep(5)
            self.parser()
            self.verify()
            self.initStatus()
        except BaseException:
            print "Problem in running the service check."

    def setClassVariables(self):
        if self.aws:
            self.sudo = True
            self.setsudo = "sudo"
            self.setsudoservice = self.setsudo + " " + "service"
        else:
            self.sudo = False
            self.setsudo = ""
            self.setsudoservice = "service"
        self.result = {}
        self.flag = []
        self.switch = None
        self.parsedresult = {}
        #This is a workaround to evaluate the service name correctly since the json parser is not reading the config file corectly for this service due to some parser / escape sequence issue.
        if self.sever_type == "ma-api":
            self.services = { self.sever_type: "nds_ma-api" }
        else:
            self.services = { self.sever_type: self.cfg[self.sever_type]["service"] }
        self.workaround = {}
        for service in self.services:

            service = self.services[service]
            down_header = service + "_DOWN"
            down_header_report = "[WARNING] \'%s\' service is DOWN." % (
                service)
            down_header_workaround = "[ACTION] Can not able to bring the service up.Please check and restart the service \'%s\' accordingly." % (
                service)
            up_header = service + "_UP"
            up_header_report = "[INFO] \'%s\' service is UP." % (service)
            up_header_workaround = "[ACTION] No action is required on the service \'%s\'." % (
                service)

            if not self.workaround:
                self.workaround = {
                    down_header: {
                        "report": down_header_report,
                        "workaround": down_header_workaround},
                    up_header: {
                        "report": up_header_report,
                        "workaround": up_header_workaround}}
            else:
                self.workaround.update({
                    down_header: {"report": down_header_report, "workaround": down_header_workaround},
                    up_header: {"report": up_header_report, "workaround": up_header_workaround}})

    def setServer(self):
        self.coresearch = self.cfg[self.sever_type]["corelocation"]

    def parser(self):
        for service in self.result.keys():
            if len(self.result[service]) == 0:
                if not self.parsedresult:
                    self.parsedresult = {service: 'no_such_service'}
                else:
                    self.parsedresult.update({service: 'no_such_service'})
            else:
                if isinstance(self.result[service], list):
                    if not self.parsedresult:
                        self.parsedresult = {service: str(
                            self.result[service][0].split()[2])}
                    else:
                        self.parsedresult.update(
                            {service: str(self.result[service][0].split()[2])})
                else:
                    if not self.parsedresult:
                        self.parsedresult = {service: str(
                            self.result[service].split()[2])}
                    else:
                        self.parsedresult.update(
                            {service: str(self.result[service].split()[2])})

    def verify(self):
        self.flag = []
        for service in self.parsedresult:
            if self.parsedresult[service] == 'running':
                pass  # self.flag.append(service+'_UP')
            else:
                service = service.lstrip("u").rstrip(":")
                self.flag.append(service + '_DOWN')

    def initStatus(self):
        if not self.flag or self.skipworkaround == False:
            self.checkForCoreFiles()
            self.finalStatus()
            return False
        else:
            self.checkForCoreFiles()
            self.performWorkaround()

    def checkForCoreFiles(self):
        try:
            self.coreSearch = self.run(
                '%s ls -lrt %s' %
                (self.setsudo, self.coresearch), sudo=self.sudo)
            if len(self.coreSearch) == 0:
                self.coreSearch = False
            elif self.coreSearch.split()[1] == "cannot" and self.coreSearch.split()[2] == "access":
                self.coreSearch = False
            else:
                self.coreSearch = eval(self.coreSearch)
        except BaseException:
            #print "problem in tracing the core files.Please check manually for the existence of core file."
            self.coreSearch = False

    def performWorkaround(self):
        TestService.max_reties += 1
        for flags in self.flag:
            self.run(
                '%s %s restart' %
                (self.setsudoservice,
                 flags.strip("_DOWN")),
                sudo=self.sudo)
        if TestService.max_reties <= 1:
            self.execute()
        else:
            self.finalStatus()

    def finalStatus(self):
        summaryreport[self.cache_key].append("SERVICE(S) REPORT")
        summaryreport[self.cache_key].append("\t ANALYSIS:")
        if not self.flag:
            summaryreport[self.cache_key].append(
                "[INFO] All the services are made up and verified all are running.")
        else:
            for flags in self.flag:
                summaryreport[self.cache_key].append(
                    self.workaround[flags]["report"])
            if self.coreSearch:
                summaryreport[self.cache_key].append(
                    "[WARNING] There were some traces of the existence of the core files.Please refer the the workaround section to know the details of the core files.")
            else:
                summaryreport[self.cache_key].append(
                    "[WARNING] There were no traces for the existence of the core files in the system.")
            TestService.service_concern.append(True)
        summaryreport[self.cache_key].append("\t WORK-AROUND:")
        if not self.flag:
            summaryreport[self.cache_key].append(
                "[NO_ACTION] No actions required since all the services healthy and running.")
        else:
            for flags in self.flag:
                summaryreport[self.cache_key].append(
                    self.workaround[flags]["workaround"])
            if self.coreSearch:
                summaryreport[self.cache_key].append(
                    "[ACTION] Below are the traces of the core files found in the system and it is being suscpected that this could have the reason for services been down.")
                for corefiles in self.coreSearch:
                    summaryreport[self.cache_key].append(("\t %s" % corefiles))
        summaryreport[self.cache_key].append("END REPORT")

    def tearDown(self):
        TestService.service_concern = [] 
        TestService.max_reties = 0
        super(TestService, self).close()
