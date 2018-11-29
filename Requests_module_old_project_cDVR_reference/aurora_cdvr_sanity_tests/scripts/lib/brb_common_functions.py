#!usr/bin/python
import os
import json
import sys
import time
import requests
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

    def write_or_edit_fie_srt(self, srt_cache):
        """
        Routine to write the SRT file to be posted to RM.
        """
        fd = open('static_route_table.txt', 'w')
        for lines in srt_cache:
            fd.write(lines)
        print "Successfully compiled the srt file to be pushed to RRs."

    def compile_raw_format_srt(self, srt):
        """
        Routine to compile the user's raw data to RM understandable format.
        """
        srt_cache = []
        isaws = False
        if sys.argv[1].startswith('aws'):isaws = True
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
      
    def post_to_rm_srt(self, cfg):
        """
        Core routine which post the user customized SRT file to RM.
        """
        isaws = False
        if sys.argv[1].startswith('aws'):isaws = True
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

    def delete_srt(self, cfg):
        """
        Delete the srt file in all the RM instances.
        :param cfg:
        :return:
        """
        isaws = False
        if sys.argv[1].startswith('aws'): isaws = True
        if isaws:
            rrhosts = self.consul_activity_srt(cfg)
        else:
            rrhosts = [cfg["rm"]["host"]]
        print "RRs in which SRT file will be deleted : ", rrhosts

        # Establishing the remote connection to RRs with paramiko to push customized the SRT file.
        for rr in rrhosts:
            print "Deleting the SRT file in : ", rr
            client1 = client.SSHClient()
            client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if isaws: client1.connect(rr, username="centos", allow_agent=True)
            else:client1.connect(rr, username="root", password="generic@123", look_for_keys=False, allow_agent=True)

            client1.exec_command("sudo rm -f /opt/cisco/gosrm/ConfigFiles/rioRecorder/static_route_table.txt")
            client1.close()
        print "Successfully deleted the SRT file in all the rr instances."

    def rename_srt_file(self, cfg, file_name):
        """
        To rename the SRT file to some other name
        :return:
        """
        isaws = False
        if sys.argv[1].startswith('aws'):
            isaws = True
        if isaws:
            rrhosts = self.consul_activity_srt(cfg)
        else:
            rrhosts = [cfg["rm"]["host"]]
        print "RRs in which SRT file will be renamed : ", rrhosts

        # Establishing the remote connection to RRs with paramiko to push customized the SRT file.
        for rr in rrhosts:
            print "Renaming the SRT file in : ", rr
            client1 = client.SSHClient()
            client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if isaws: client1.connect(rr, username="centos", allow_agent=True)
            else:client1.connect(rr, username="root", password="generic@123", look_for_keys=False, allow_agent=True)

            value = (
                "sudo mv /opt/cisco/gosrm/ConfigFiles/rioRecorder/"
                "static_route_table.txt /opt/cisco/gosrm/ConfigFiles/"
                "rioRecorder/{0}.txt".format(file_name))
            client1.exec_command(value)
            time.sleep(0.5)
            stdin, stdout, stderr = client1.exec_command("ls /opt/cisco/gosrm/ConfigFiles/rioRecorder/")
            print stdout.readlines()
            client1.close()
        print "Successfully renamed the SRT file in all the rr instances."

    def modify_srt(self, cfg, srt):
        """
        Entry routine which the users get exposed to.
        """
        try:
            compiled_data = self.compile_raw_format_srt(srt)
            self.write_or_edit_fie_srt(compiled_data)
            self.post_to_rm_srt(cfg)

        except Exception,e:
            print str(e)
            message = "Testcase Failed: Issue in pushing the SRT file to rr."
            print message
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
        url = "http://" + rm_host + "/emdata/RecRouter/global/RR/Configuration"
        payload = {"StaticRouting": state}
        headers = {}
        response = requests.request("PUT", url, data=payload, headers=headers)
        res_content = json.loads(response.content)
        if response.status_code != 200:
            raise Exception("Unable to change the SRT availability.")
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


    def get_rr_regions_list(self, cfg):
        """
        Fetch Recording Region List
        :return status, response
        """

        rm_host = cfg["rm"]["host"]
        url = "http://" + rm_host + "/emdata/ResourceManager/Resources"
        response = requests.request("GET", url)
        if response.status_code != 200:
            return False, response
        else:
            res_content = json.loads(response.content)
            return True, res_content


if __name__ == "__main__":
    scriptName = os.path.basename(__file__)
    #read config file
    sa = sys.argv
    cfg = relative_config_file(sa,scriptName)
    #Example
    configureSRT_instance = ConfigureSRT()
    configureSRT_instance.modify_srt(cfg, [["LWR-DMZ-1", "*", "LWR-DMZ-1", "NoChange"]])

