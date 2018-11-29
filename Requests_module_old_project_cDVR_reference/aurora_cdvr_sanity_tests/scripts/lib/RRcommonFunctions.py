#!/usr/bin/python

import sys
import requests
import json
from subprocess import Popen, PIPE
import paramiko
from paramiko import client

class ConfigureSRT(object):
    """
    This module helps to change the SRT
    with the user customized data in RM belogs to the lab.
    Syntax:
        <instance> = ConfigureSRT()
        <instance>.modify_srt( [ [ <SourceRegion>, <SourceCopy>, <DestinationRegion>, <DestinationCopy>], .... ] )
    Example:
        configureSRT_instance = ConfigureSRT()
        configureSRT_instance.modify_srt(cfg, [["LWR-DMZ-1", "*", "LWR-DMZ-1", "common"]])
    """
    def exec_cmd(self, command_list):
        """
        Routine to execute the local commands.
        """
        try:
            cmd = Popen(command_list, stdout=PIPE, stderr=PIPE)
            return (True, cmd.communicate())
        except subprocess.CalledProcessError:
            return (False, cmd.communicate())

    def consul_activity_srt(self, cfg):
        """
        Routine to send the callback to exec_cmd and collect the running rm IPs in the concerned lab.
        """
        try:
            rrhosts = []
            consul_host = cfg["consul"]["host"]
            consul_port = cfg["consul"]["port"]
            consul_ec_search_api = cfg["consul"]["running_instances_collection_api"]
            curl_string = str(consul_host) + ':' + str(consul_port) + str(consul_ec_search_api)
            print "curl_string : ", curl_string
            command_list = ["curl", curl_string]
            cmd_res, cmd_op = self.exec_cmd(command_list)
            assert cmd_res, "Testcase Failed: Can not execute the local command."
            if cmd_res:
                consulop = cmd_op[0]
                jdata = json.loads(consulop)
                for service in jdata:
                    if "-rr-" in service["Node"] and service["TaggedAddresses"] != None:
                        rrhosts.append(service["Address"])
                return rrhosts
        except AssertionError as ae:
            print "ERROR :", str(ae)
            return []


    def write_or_edit_fie_srt(self, srt_cache):
        """
        Routine to write the SRT file to be posted to RM.
        """
        try:
            fd = open('static_route_table.txt', 'w')
            for lines in srt_cache:
                fd.write(lines)
            print "Successfully compiled the srt file to be pushed to RRs."
            return True
        except Exception as e:
            print "ERROR :", str(e)
            return False

    def compile_raw_format_srt(self, srt):
        """
        Routine to compile the user's raw data to RM understandable format.
        """
        srt_cache = []
        isaws = False
        try:
            if sys.argv[-1].startswith('aws'):isaws = True
            if len(srt) == 0:
                message = "No entries given for SRT."
                print message
                return False
            for entries in srt:
                if len(entries) == 0:
                    line = '\n'
                    srt_cache.append(line)
                else:
                    line = '|'.join(entries)
                    #line += "||"
                    print "Compiled the data to be entered in the SRT file : ", line
                    srt_cache.append(line)
                srt_cache.append("\n")
            return srt_cache
        except Exception as e:
            print "ERROR :", str(e)
            return []

    def post_to_rm_srt(self, cfg):
        """
        Core routine which post the user customized SRT file to RM.
        """
        try:
            isaws = False
            if sys.argv[-1].startswith('aws'):isaws = True
            if isaws:rrhosts = self.consul_activity_srt(cfg)
            else:rrhosts = [cfg["rm"]["host"]]
            print "RRs to be posted with the customized SRT : ", rrhosts

            # Establishing the remote connection to RRs with paramiko to push customized the SRT file.
            for rr in rrhosts:
                print "Posting the customized SRT to rr : ", rr
                client1 = client.SSHClient()
                client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if isaws: client1.connect(rr, username="centos", allow_agent=True)
                else:client1.connect(rr, username="root", password="generic@123", look_for_keys=False, allow_agent=True)

                sftp = client1.open_sftp()
                sftp.put("static_route_table.txt", "/tmp/static_route_table.txt")
                sftp.close()

                client1.exec_command("sudo rm -f /opt/cisco/gosrm/ConfigFiles/rioRecorder/static_route_table.txt")
                client1.exec_command("sudo chown root /tmp/static_route_table.txt")
                client1.exec_command("sudo chgrp root /tmp/static_route_table.txt")
                client1.exec_command("sudo cp -f /tmp/static_route_table.txt /opt/cisco/gosrm/ConfigFiles/rioRecorder/static_route_table.txt")
                client1.exec_command("sudo rm -f /tmp/static_route_table.txt")
                client1.close()
            print "Successfully pushed the customized SRT file to all the rr instances."
            return True
        except Exception as e:
            print "ERROR :", str(e)
            return False

    def modify_srt(self, cfg, srt):
        """
        Entry routine which the users get exposed to.
        """
        try:
            compiled_data = self.compile_raw_format_srt(srt)
            assert compiled_data != [], "Compiled data is Empty"
            assert self.write_or_edit_fie_srt(compiled_data), "Unable to write SRT file"
            assert self.post_to_rm_srt(cfg), "Unable to push the SRT file"
            return True
        except AssertionError as e:
            print str(e)
            print "Testcase Failed: Unable to modify the SRT table"
            return False

    def change_srt_file(self, cfg, srt_name="static_route_table.txt", revert=False, default_srt="static_route_table.txt"):
        """
        Core routine to rename the SRT file in RM.
        """
        try:
            isaws = False
            if sys.argv[-1].startswith('aws'):isaws = True
            if isaws:rrhosts = self.consul_activity_srt(cfg)
            else:rrhosts = [cfg["rm"]["host"]]
            print "RR list: ", rrhosts

            # Establishing the remote connection to RRs with paramiko to push customized the SRT file.
            for rr in rrhosts:
                print "Renaming the SRT in rr : ", rr
                client1 = client.SSHClient()
                client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if isaws: client1.connect(rr, username="centos", allow_agent=True)
                else:client1.connect(rr, username="root", password="generic@123", look_for_keys=False, allow_agent=True)

                if revert:
                    i, o, e = client1.exec_command("mv /opt/cisco/gosrm/ConfigFiles/rioRecorder/%s /opt/cisco/gosrm/ConfigFiles/rioRecorder/%s" %(srt_name, default_srt))
                else:
                    i, o, e = client1.exec_command("mv /opt/cisco/gosrm/ConfigFiles/rioRecorder/%s /opt/cisco/gosrm/ConfigFiles/rioRecorder/%s" %(default_srt, srt_name))

                #print "Output :", str(o)
                #if e:
                #    print "Error : ", str(e)
                client1.close()
                time.sleep(1)

            print "Successfully Renamed the SRT file in all rr instances."
            return True
        except Exception as ex:
            print "Exception :", str(ex)
            return False

    def check_srt_status(self, cfg, state="Enable"):
        """
        Routine to check the status of the SRT
        """
        rm_host = cfg["rm"]["host"]
        vsrm_ips = []
        url = "http://" + rm_host + "/emdata/RecRouter/global/RR/Configuration"
        headers = {}
        response = requests.request("GET", url, headers=headers)
        res_content = json.loads(response.content)
        if response.status_code != 200:
            raise Exception("Unable to get the SRT availability")
        else:
            for vsrm in res_content:
                if vsrm.get("StaticRouting") == state:
                    continue
                else:
                    vsrm_ips.append(vsrm.get("vsrmIp"))
        if vsrm_ips:
            msg = ''.join(vsrm_ips) + " are not in %s state" % state
            return False, msg
        else:
            return True, "VSRM is in %s state" % state

    def set_srt_availability(self, cfg, state="Enable"):
        """
        Routine to enable/diable the SRT
        """
        rm_host = cfg["rm"]["host"]
        vsrm_ips = []

        isaws = False
        if sys.argv[-1].startswith('aws'): isaws = True
        if isaws:
            rrhosts = self.consul_activity_srt(cfg)
        else:
            rrhosts = [cfg["rm"]["host"]]
        print "RR list: ", rrhosts

        # Establishing the remote connection to RRs with paramiko to push customized the SRT file.
        for rr in rrhosts:

            url = "http://" + rr + "/emdata/RecRouter/global/RR/Configuration"
            payload = '{"StaticRouting": "%s"}'%state
            headers = {}
            print "Update the SRT availability via url :", url
            response = requests.request("PUT", url, data=payload, headers=headers)
            if response.status_code != 200:
                print response.status_code
                print response.content
                return False, "Unable to change the SRT availability."
            else:
                res_content = json.loads(response.content)
                for vsrm in res_content:
                    if vsrm.get("StaticRouting") == state:
                        continue
                    else:
                        vsrm_ips.append(vsrm.get("vsrmIp"))
        if vsrm_ips:
            msg = ' '.join(vsrm_ips) + " are not in %s state" % state
            return False, msg
        else:
            return True, "VSRM is in %s state" % state

if __name__ == "__main__":
    print "Importing module RRcommonFunctions."

