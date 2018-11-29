#!/usr/bin/env python

import sys

class Report(object):
        """
        This will parse the basic engine's summary report and calulate the 
          - Total TCs Failed
          - Total TCs with Warnings
          - Total TCs Skipped

        Usage:
             report_obj = Report()
             report_obj.parse_summary('<basic.log>')
          
             Once the above is done, we can get the errors, warning and skipped TCs as below respectively,             
             ERRORS = report_obj.total_errors()
             WARNINGS = report_obj.total_warnings()
             SKIPPED = report_obj.total_skip()
        """

        def __init__(self):
            self.finaldict = {}
            self.eror_count = 0
            self.warning_count = 0
            self.skip_count = 0
            
	def parse_summary(self, filename):
	    log = filename
	    filedesc = open(log, 'r')
	    statuscolumn = 1
	    testname = 0
	    ERR = '1'
	    WARN = '2'
	    SKIP = '3'
	    skip = True
	    for line in filedesc.readlines():
	        if not 'Summary' in line and skip == True:
	            continue
	        else:
	            skip = False
	            if line.startswith('basic'):
	                TC = line.split()[testname]
	                RC = line.split()[statuscolumn]
	                if RC == ERR:
	                    self.eror_count += 1
	                    self.finaldict.update({TC:{'RC' : RC, 'STATUS' : 'ERROR'}})
	                if RC == WARN:
	                    self.warning_count += 1
	                    self.finaldict.update({TC:{'RC' : RC, 'STATUS' : 'WARN'}})
	                else:
	                    self.skip_count += 1
	                    self.finaldict.update({TC:{'RC' : RC, 'STATUS' : 'SKIP'}})
	    return self.finaldict
	
	def total_warnings(self):
	    return self.warning_count
	def total_errors(self):
	    return self.eror_count
	def total_skip(self):
	    return self.skip_count
	
if __name__ == "__main__":
    myreport = Report()
    #myreport.parse_summary(filename='basic-feature_040106-20180125.log')
