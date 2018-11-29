#/usr/bin/python

import os
import re
import time
import json
import unicodedata
from collections import OrderedDict
from subprocess import Popen, PIPE
from paramiko import client

summaryreport = {}


class MockTerminal(object):
    """
    """

    def __init__(
            self,
            address,
            username,
            password=None,
            sever_type=None,
            pemfile=None,
            aws=False,
            cfg=None):
        self.tims_list = []
        self.response = ''
        self.cfg = cfg
        self.address = address
        self.username = username
        self.password = password
        self.sever_type = sever_type
        self.pemfile = pemfile
        self.client = None
        self.aws = aws
        self.cache_key = str(self.address) + "_" + str(self.sever_type)

        # Fix for not adding the consul ip in the output dictionary.
        if not self.sever_type is None:
            summaryreport.update({self.cache_key: []})

        # Fix for setting the agent to pass the key file to script to login to the specified node.
        if password is None and pemfile is None:
            self.allow_agent = True

        # Let the user know we're connecting to the server
        # print "Connecting to server."
        # Create a new SSH client

    def setConnection(self):
        try:
            self.client = client.SSHClient()
            # The following line is required if you want the script to be able
            # to access a server that's not yet in the known_hosts file
            self.client.set_missing_host_key_policy(client.AutoAddPolicy())
            if self.password is None and self.pemfile is not None:
                try:
                    self.client.connect(
                        self.address,
                        username=self.username,
                        key_filename=self.pemfile,
                        timeout=10)
                except BaseException:
                    return False
            elif self.pemfile is None and self.password is not None:
                try:
                    self.client.connect(
                        self.address,
                        username=self.username,
                        password=self.password,
                        look_for_keys=False,
                        timeout=10)
                except BaseException:
                    return False
            else:
                try:
                    self.client.connect(
                        self.address,
                        username=self.username,
                        allow_agent=self.allow_agent,
                        timeout=10)
                except BaseException:
                    return False
        except BaseException:
            print "Problem in establishing the connection."

    def run(self, command, local=False, statusonly=True, sudo=False):
        try:
            if local:
                return self._run_local(command, statusonly, sudo)
            else:
                return self._run_remote(command, sudo)
        except BaseException:
            print "Problem in running the command."

    def _run_local(self, command, statusonly=True, sudo=False):
        # print "Running the command %s in local machine..."% (command)
        if statusonly:
            status = Popen(command.split(), stdout=PIPE, stderr=PIPE)
            output = status.communicate()
            status = status.poll()
            return status
        else:
            status = Popen(command.split(), stdout=PIPE, stderr=PIPE)
            output = status.communicate()
            return output[0]

    def _run_remote(self, command, sudo=False):
        if sudo:
            return self._run_remote_sudo_user(command)
        else:
            return self._run_remote_normal_user(command)

    def _run_remote_normal_user(self, command):
        try:
            # print "Running command : %s"% (command)
            stdin, stdout, stderr = self.client.exec_command(command)
            # print "stdin : %s\n, stdout : %s\n, stderr : %s"%
            # (stdin.readlines(), stdout.readlines(), stderr.readlines())
            self.response = stdout.readlines()
        except BaseException:
            self.response = 'CONNECTION_CLOSED'
            return self.response
        finally:
            return self.response

    def _run_remote_sudo_user(self, command):
        status = Popen(["ssh",
                        "-t",
                        #"-i",
                        #"%s" % (self.pemfile),
                        "{0}".format(self.address),
                        "{0}".format(command)],
                       stdout=PIPE,
                       stderr=PIPE)
        output = status.communicate()
        return output[0]

    def getTims(self):
        return self.tims_list

    def close(self):
        self.client.close()
