"""
UpdateResults.py module is used to update the Test Case Result in Rally.
The test results are read from the JSON file.

It requires python's pyral and request modules installed.

pyral - https://pypi.python.org/pypi/pyral
request - https://pypi.python.org/pypi/requests

We need to have the apikey generated from rally to update the results.
-https://rally1.rallydev.com/login/accounts/index.html#/apps
"""

import json
import sys
import os
from pyral import Rally
import requests
import datetime
import time
#from requests.packages.urllib3.exceptions import InsecureRequestWarning
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------------------ GLOBAL CONSTANTS -----------------------------------
apikey = "_SAH5hxQuSHujfna1TOym0E0MI3hykT7uzo3AheZrhc"
wrkspc = "SPVSS"
project = "Republic-Cruiser"

URL = "https://rally1.rallydev.com/slm/webservice/v3.0/testcaseresult/create"
rally_url = "rally1.rallydev.com"

approved_modules = ("basic-feature", "corner", "hitless")
allowed_results = ("Pass", "Fail", "Error", "Blocked")

timeout = 5
result_file_name = "ec_results.json"
# -------------------------------------------------------------------------------------


def send_url(method, url, server_timeout=None, header=None, payload_content=None):
    """
    Make the request to the API method.
    """

    try:
        if method == "post":
            r = requests.post(url, data=payload_content, headers=header, timeout=server_timeout, allow_redirects=True)
            return r
        elif method == "put":
            r = requests.put(url, data=payload_content, headers=header, timeout=server_timeout, allow_redirects=True)
            return r
        elif method == "delete":
            r = requests.delete(url, data=payload_content, headers=header, timeout=server_timeout, allow_redirects=True)
            return r
        else:
            r = requests.get(url, headers=header, timeout=server_timeout, verify=False, allow_redirects=True)
            return r
    except requests.exceptions.RequestException as error:
        print error
        print "Problem accessing ...... " + url
    return None


class ReadJson(object):
    def __init__(self, result_file=result_file_name, note_prefix="Automation"):
        try:
            self.result_file = result_file

            self.notes = note_prefix + " : "
            self.rally = None
            self.workspace = None
            self.result_json = None
            self.run_date = None
            self.build = None
        except Exception as e:
            print "Exception :\n", str(e)

    def read_result(self):
        try:
            print "Read the Result from JSON file"
            assert os.path.exists(self.result_file), "Result file %s not present" % self.result_file
            print "Result file : ", self.result_file
            res_file = open(self.result_file, "r")
            self.result_json = json.load(res_file)

            print "\nEstablishing the connection"
            self.rally = Rally(rally_url, apikey=apikey, workspace=wrkspc, project=project, verify_ssl_cert=False)

            assert self.rally, "Unable to communicate to Rally"

            _wksp = self.rally.getWorkspace()
            self.workspace = str(_wksp.ref)
            assert self.workspace, "Unable to get the Workspace reference"
            print "Workspace :", self.workspace

            self.run_date = str(datetime.datetime.utcnow().isoformat())
            print "Run Date : ", self.run_date

            self.build = str(self.result_json['config']['gitlastcommit'])
            print "Build : ", self.build

            self.notes = self.notes + str(self.result_json['config']['labname']) + " : "
            return True

        except Exception as e:
            print "Exception in read_result :\n", str(e)
            return False

    def update_result(self):
        try:
            headers = {
                        'zsessionid': apikey,
                        'Content-Type': 'application/json'
                       }

            print "\nHeaders :", headers

            # Verify the testsuite key is present in the ec_result.json
            assert 'testsuite' in self.result_json, "'testsuite' is not present in the Result JSON"

            result_testsuite = self.result_json['testsuite'].keys()
            print "Modules present in ec_result.json : ", result_testsuite

            allowed_modules = [mdl for mdl in result_testsuite if mdl in approved_modules]

            print "Modules allowed to update the result :", allowed_modules

            testcase_list = {}
            skipped_testcase = []
            final_list = []
            update_failed = []

            for mdl in allowed_modules:
                testcase_list.setdefault(mdl, [])
                for tc in self.result_json['testsuite'][mdl]:
                    tc_format_id = str(tc['TC'])
                    try:
                        testcase_list[mdl].append(tc_format_id)

                        tcname, tcresult, tc_duration, notes = self.get_testcase_details(tc, tc_format_id)

                        if tcresult is None or tcresult == "SKIPPED":
                            skipped_testcase.append(tc_format_id)
                            continue

                        print "TestCase id of %s is %s Result : %s Duration : %s" \
                              % (tc_format_id, tcname, tcresult, tc_duration)

                        res1, payload = self.post_result(headers, self.build, tcname, self.run_date,
                                                         tcresult, self.workspace, tc_duration, notes)

                        if res1 is None:
                            update_failed.append(tc_format_id)
                            continue

                        if res1.status_code != 200:
                            print "#######################################"
                            print "Update Failed for %s" % tc_format_id
                            print "Status Code : ", res1.status_code
                            print "#######################################"
                            update_failed.append(tc_format_id)
                            continue

                        res = json.loads(res1.content)
                        if res['CreateResult']['Errors']:
                            print "#######################################"
                            print "Update Failed for %s" % tc_format_id
                            print "Error :", res['CreateResult']['Errors']
                            print "Payload : ", payload
                            print "#######################################"
                            update_failed.append(tc_format_id)
                            continue

                        final_list.append(tc_format_id)
                    except Exception as e:
                        print "\nException when updating ", tc_format_id, "\nError : ", str(e)
                        update_failed.append(tc_format_id)

            print "\n", "#" * 10, " SUMMARY ", "#" * 10
            print "\nTest Results updated for : ", final_list
            print "\nTest Case not Present :", skipped_testcase
            print "\nTest case failed to update result :", update_failed
            print "\nTest Case Complete Set : ", testcase_list
            print "#" * 10, " SUMMARY ", "#" * 10, "\n"

            # Make a second Try for the Failed to update test cases
            if update_failed:
                time.sleep(5)
                update_failed2 = []
                update_success = []
                for failedtc in update_failed:
                    print "Retry update results for ", failedtc
                    srchmodule = [k for k, v in testcase_list.items() if failedtc in v][0]

                    testcase_li = self.result_json['testsuite'][srchmodule]

                    for tc in testcase_li:
                        if tc['TC'] == failedtc:
                            tcname2, tc_res, tc_duration2, notes2 = self.get_testcase_details(tc, failedtc)
                            if tc_res is None or tc_res == "SKIPPED":
                                update_failed2.append(failedtc)
                            else:

                                print "Retry TestCase %s Result : %s Duration : %s" % (failedtc, tc_res, tc_duration2)

                                res2, pl = self.post_result(headers, self.build, tcname2, self.run_date,
                                                            tc_res, self.workspace, tc_duration2, notes2)

                                if res2 is None or res2.status_code != 200:
                                    update_failed2.append(failedtc)
                                    continue
                                res = json.loads(res2.content)
                                if res['CreateResult']['Errors']:
                                    update_failed2.append(failedtc)
                                    continue

                                update_success.append(failedtc)

                if update_failed2 or update_success:
                    print "\n", "#" * 10, " RETRY SUMMARY ", "#" * 10
                    print "\nUpdate failed again :", update_failed2
                    print "\nUpdate successfull in the seconds attempt :", update_success
                    print "#" * 10, " RETRY SUMMARY ", "#" * 10

            return True

        except Exception as ae:
            print "Exception in update_result:\n", str(ae)
            return False

    def get_testcase_details(self, tc, tc_format_id):
        try:
            # Get the Test Case name
            tcname = self.get_testcase_name(tc_format_id)
            if not tcname:
                # print "Test case Skipped : ", tc_format_id
                return tc_format_id, "SKIPPED", None, None

            tcresult = str(tc['status'])
            assert tcresult, "Test Result not found for %s" % tc_format_id
            tcresult = tcresult.capitalize()
            if tcresult not in allowed_results:
                print "TestCase %s status is %s , so marking as 'Inconclusive'" % (tc_format_id, tcresult)
                tcresult = "Inconclusive"

            tc_duration = tc['time']
            if not tc_duration:
                tc_duration = "0.0"
            # Converting the float to 2 decimal place
            tc_duration = "{0:.2f}".format(float(tc_duration))

            notes = tc['message']
            if notes:
                if "EXCEPTION" in notes:  # If there is a Script Exception it wont be printed in the notes
                    notes = self.notes + " Exception in Script"
                else:
                    notes = self.notes + str(notes)
            else:
                notes = self.notes

            return tcname, tcresult, tc_duration, notes

        except Exception as e:
            print "Error in getting the details of ", tc_format_id, " Error : ", str(e)
            return tc_format_id, None, None, None

    def post_result(self, headers, build, tc_name, run_date, tc_result, workspace, duration, notes):
        payload = None
        try:
            payload = """{"TestCaseResult":
                                        {
                                        "Build":"%s",
                                        "TestCase":"%s",
                                        "Date":"%s",
                                        "Verdict":"%s",
                                        "Workspace":"%s",
                                        "Duration":"%s",
                                        "Notes":"%s"
                                        }
                                    }
                                """ % (build, tc_name, run_date, tc_result, workspace, duration, notes)

            r = send_url("post", URL, timeout, headers, payload)

            return r, payload

        except Exception as ae:
            print "Exception in post_result :\n", str(ae)
            return None, payload

    def get_testcase_name(self, tc):
        try:
            # print "Test Case :",tc
            name = self.rally.get('TestCase', query='FormattedID = "%s"' % tc, fetch=True, projectScopeUp=True)
            assert name.data['Results'], "Unable to find the Testcase %s" % tc
            assert name.data['Results'][0]['ObjectID'], \
                "Unable to get the details of the Testcase %s \nData Fetched %s" % (tc, name.data['Results'])

            tcname = "testcase/%s" % (name.data['Results'][0]['ObjectID'])
            return str(tcname)
        except Exception as e:
            print "Exception while retrieving the testcase %s :\n%s" % (tc, str(e))
            return None


def main():
    try:
        sa = sys.argv
        if len(sa) == 2:
            result = sa[1]
            rj = ReadJson(result_file=result)
        else:
            rj = ReadJson()
        assert rj.read_result(), "Error in Read Result"
        assert rj.update_result(), "Error in Update Result"
        return True
    except Exception as e:
        print "Exception :\n", str(e)
        return False

if __name__ == "__main__":
    main()
