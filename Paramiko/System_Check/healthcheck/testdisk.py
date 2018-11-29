#/usr/bin/python

from mockterminal import MockTerminal, summaryreport


class TestDisk(MockTerminal):
    """
    """
    disk_concern = []

    def execute(self):
        try:
            self.setClassVariables()
            self.result = self.run('df -h')
            self.parser()
            self.verify()
            self.status()
        except BaseException:
            print "Problem in running the disk check for this server."

    def setClassVariables(self):
        self.workaround = {
            "ALMOSTFULL": {
                "report": "[WARNING] Sytem's disk space on the partition %s is almost FULL and is about %s.",
                "workaround": "[ACTION] Make some free space on the partition %s in the system by cleaning up the unwanted files."},
            "CRITICAL": {
                "report": "[WARNING] Sytem's disk space on the partition %s is FULL and is about %s.",
                "workaround": "[ACTION] Make some free space on the partition %s in the system by cleaning up the unwanted files."},
            "FREE": {
                "report": "[INFO] System's disk space on partion %s is free and is about %s.",
                "workaround": "[ACTION] No actions required on the partition %s."}}
        self.result = None
        self.flag = {}
        self.parsedresult = []

    def parser(self):

        self.temp = []
        count = 0
        counter = 0

        for res in self.result[1:]:
            stripped = res.strip()
            if len(stripped.split()) == 1:
                self.temp.append(stripped)
                count = 1
            elif count == 1:
                self.temp.extend(stripped.split())
                self.parsedresult.append(self.temp)
                self.temp = []
                count = 0
            else:
                self.parsedresult.append(stripped.split())

    def verify(self):
        for device in self.parsedresult:
            if int(device[4].rstrip("%")) < 97:
                pass
            if int(
                    device[4].rstrip("%")) >= 97 and int(
                    device[4].rstrip("%")) < 98:
                self.flag.update({device[0]: {"ALMOSTFULL": device[4]}})
                # print "Moderate."
            elif int(device[4].rstrip("%")) >= 98 and int(device[4].rstrip("%")) < 99:
                self.flag.update({device[0]: {"ALMOSTFULL": device[4]}})
                # print "Moderate To High."
            elif int(device[4].rstrip("%")) >= 99:
                self.flag.update({device[0]: {"CRITICAL": device[4]}})
                # print "High And Almost Full."

    def status(self):
        summaryreport[self.cache_key].append("DISKUSAGE(S) REPORT")
        summaryreport[self.cache_key].append("\t ANALYSIS:")
        if not self.flag:
            summaryreport[self.cache_key].append(
                "[INFO] All the partition in the system have enough space.")
        else:
            for devices in self.flag:
                for flags in self.flag[devices]:
                    summaryreport[self.cache_key].append(
                        self.workaround[flags]["report"] % (devices, self.flag[devices][flags]))
            TestDisk.disk_concern.append(True)
        summaryreport[self.cache_key].append("\t WORK-AROUND:")
        if not self.flag:
            summaryreport[self.cache_key].append(
                "[NO_ACTION] No actions required since all the partion in the system has enough space.")
        else:
            for devices in self.flag:
                for flags in self.flag[devices]:
                    summaryreport[self.cache_key].append(
                        self.workaround[flags]["workaround"] % (devices))
        summaryreport[self.cache_key].append("END REPORT")

    def tearDown(self):
        super(TestDisk, self).close()
