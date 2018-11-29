#!/usr/bin/python

import os
import sys
import json
import time
import yaml
import argparse
import inspect
import datetime
from pprint import pprint
from subprocess import Popen, PIPE
import paramiko
from paramiko import client
import mypaths
from scripts.lib.L1commonFunctions import (
        relative_config_file, set_errorlogging)
from scripts.lib.L3commonFunctions import (
    updatetimsresultsjson)

# Default test component that will be run if user is not specifying any specific components to be tested.
# However it will be overridden with config in config.yaml if user is not specifying the components.
CONFIGURATION_TO_BE_TESTED = ["PPS"]
TEXT = "text"
JSON = "json"
YAML = "yaml"
DEFAULT_LOG_KEY = "Default"
RUNNING_LOG_KEY = "Running"
MISSING_KEY = "Missing"

class Register(dict):

    """
    This is the base class for the TC.
    Register class will register thye components that are to be tested.
    It addition, it maintains all the components important arguments.
    """
    # This dict object is to maintain the component class's object and its parsed data.
    registry = {}
    # Index for tracking the number of iteration of
    # instantiation of the component classes across categories.
    index = 0
    # This is used to maintain the logging data.
    logger_data = []
    # This is the marigin length from where the dot starts while printing the results.
    length_of_column = 80
    # This is to handle the alignmet of the results.
    alignment_type = ' '
    # This is the tag used to give an hintful update or sort of warning
    # to user about the wrongly configurable host though we track the details in log file.
    fail_tag = {}
    # Prefix to confim the environment(normal/cloud) of test and accordingly perform the actions
    cloud_environment_prefix = "aws"
    def __init__(self, class_object):
        self.register(class_object)
        self.save_configuration_from_remote_system()


    def register(self, class_object):
        """
        Routine to register the component classes.
        """
        self.class_name = class_object.__name__
        Register.registry.update({self.class_name : {"class_object":class_object}})

    def save_configuration_from_remote_system(self):
        """
        Routine to store the parsed configuration of the components respectively.
        """
        self.file_object = ''
        Register.registry[self.class_name].update({"file_object":self.file_object})

class Activity(Register):

    """
    This Activity class is the one where all operations such as command execution,
    file download, file parsing etc will be handled.
    This is like an interface between Register and TC execution class.
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

    def consul_activity(self, cfg, component):
        """
        Routine to send the callback to exec_cmd and collect the running component IPs in the concerned lab.
        """
        try:
            hosts = []
            component_search_prefix = cfg[component]["consul_search_string"]
            consul_host = cfg["consul"]["host"]
            consul_port = cfg["consul"]["port"]
            consul_ec_search_api = cfg["consul"]["running_instances_collection_api"]
            curl_string = str(consul_host) + ':' + str(consul_port) + str(consul_ec_search_api)
            #print "curl_string : ", curl_string
            command_list = ["curl", curl_string]
            cmd_res, cmd_op = self.exec_cmd(command_list)
            assert cmd_res, "Testcase Failed: Can not execute the local command."
            if cmd_res:
                consulop = cmd_op[0]
                jdata = json.loads(consulop)
                for service in jdata:
                    if component_search_prefix in service["Node"] and service["TaggedAddresses"] != None:
                        hosts.append(service["Address"])
                return hosts
        except AssertionError as ae:
            print "ERROR :", str(ae)
            return []

    def dict_former_based_on_delimiter(self, object_to_be_parsed, delimiter='='):
        """
        Routine that parse the list object and return it as a dict object.
        """
        configuration = {}
        for list_object in object_to_be_parsed:
            ####################################################################################
            # 1. Spliting the key and value in config file based on the delimiter specified    #
            # 2. Removes the unwanted spaces from the key and vale before forming it as a dict.#
            ####################################################################################
            split_up = [x.strip(' ') for x in list_object.split(delimiter)]
            if len(split_up) > 2:
                # Hook to regularise the split if there are more than one '=' in a configuration line.
                _split_up = "=".join(split_up[1:])
                split_up = [split_up[0], _split_up]
            cached_dict_object = dict((split_up,))
            configuration.update(cached_dict_object)

        Register.logger_data.append("%s | Successfully formed dict object and returned | \
            call back => %s." % (datetime.datetime.now(), inspect.stack()[1][3]))
        return configuration

    def text_file_parser(self, local_config, delimiter='='):
        """
        Routine that read the text file and store in ito list object
        """
        configuration = []
        with open(local_config, "r") as lines:
            for line in lines.readlines():
                if line.startswith("#"):
                    continue
                if not line[:1].isalnum():
                    continue
                else:
                    configuration.append(line.strip())
        # configuration object converted to dict object before returning the value to its callee.
        configuration = self.dict_former_based_on_delimiter(configuration, delimiter)
        Register.logger_data.append("%s | Successfully parsed text file and returned the dict \
            object | call back => %s."% (datetime.datetime.now(), inspect.stack()[1][3]))
        return configuration

    def yaml_file_parser(self, local_config):
        """
        Routine that read the yaml file and store in ito dict object
        """
        with open(local_config, "r") as yaml_file:
            data = yaml.load(yaml_file)
        Register.logger_data.append("%s | Successfully parsed the yaml file and returned the dict \
            object | call back => %s." % (datetime.datetime.now(), inspect.stack()[1][3]))
        return data

    def json_file_parser(self, local_config):
        """
        Routine that read the json file and store in ito dict object
        """
        with open(local_config, "r") as json_file:
            data = json.load(json_file)
        Register.logger_data.append("%s | Successfully parsed and returned the dict object | \
            call back => %s." % (datetime.datetime.now(), inspect.stack()[1][3]))
        return data

    def get_configuration_file(self, cfg, component, config_file_path, config_type, config_delimit="="):
        """
        Core routine which get the configuration file from remote
        server and return the parsed dict object to the call back function.
        """
        try:
            configuration = {}

            if os.environ["isaws"] == "yes":
                hosts = self.consul_activity(cfg, component=component.lower())
            else:
                hosts = [cfg[component]["host"]]
            Register.logger_data.append("Configuration files will be downloaded from %s for the \
                component %s | call back => %s" % (hosts, component.upper(), inspect.stack()[1][3]))

            for rr in hosts:
                try:
                    Register.logger_data.append("%s | Downloading and parsing of the configuration \
                        file from %s for the component %s started" % (datetime.datetime.now(), rr, component.upper()))
                    client1 = client.SSHClient()
                    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    if os.environ["isaws"] == "yes":
                        client1.connect(rr, username=cfg["username"], allow_agent=True)
                    else:
                        client1.connect(rr, username="root", password="generic@123", look_for_keys=False, allow_agent=True)

                    local_config = "/tmp/config"
                    sftp = client1.open_sftp()
                    for files in config_file_path:
                        sftp.get(files, local_config)
                        if config_type == TEXT:
                           configuration.update({rr : self.text_file_parser(local_config, \
                               delimiter=config_delimit)})
                        elif config_type == JSON:
                           configuration.update({rr : self.json_file_parser(local_config)})
                        elif config_type == YAML:
                           configuration.update({rr : self.yaml_file_parser(local_config)})
                        else:
                           Register.logger_data.append("%s | Failed: Unsupported file \
                               type and that can not be parsed." % (datetime.datetime.now()))
                except Exception as e:
                    print "ERROR :", str(e)
                finally:
                    client1.close()
                    sftp.close()
            Register.logger_data.append("%s | Successfully collected, parsed and\
                returned the dict object | call back => %s." \
                % (datetime.datetime.now(), inspect.stack()[1][3]))
            return configuration
        except Exception as e:
            print "ERROR :", str(e)
            return False
class StartComponentTest(Activity):
    """
    This StartComponentTest class is the core class for
    starting each component class object which ever got
    registered.It also takes care of the test level functionality
    such as parsing argument from user, print, saving the report etc.
    """
    def __init__(self):
        # For overriding the constructor of parent class while creating instances
        self.logging_pad = None
        self.message = ""
        self.test_id = "Test_Default_Configuration"
        self.status = 0
        self.tims_dict = {self.test_id: ["US86704", self.message, self.status],}
        os.environ["isaws"] = "no"

    def set_arguments(self, CNFG):
        self.cfg = CNFG
        if self.cfg["LABNAME"].startswith(Register.cloud_environment_prefix):
            os.environ["isaws"] = "yes"
        CONFIGURATION_TO_BE_TESTED = self.cfg["feature"]["stand-alone"]["config-test"]["nodes"]

    def _strip_arguments(self, args):
        """
        Routine used for argument level striping.
        """
        return args.strip('[').strip(']')

    def parse_arguments(self):
        """
        Routine for parsing argument from user.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("-C", "--Component", type=str, \
                        help='Components to be tested')
        parser.add_argument("-L", "--Labconfig", type=str, \
                        help='Lab configs to be used by the suite')
        parser.add_argument("-l", "--logfile", type=str, \
                        help='log file name')
        parser.add_argument("-s", "--summarylog", type=str, \
                        help='summary log file name')
        args = parser.parse_args()
        if args.Labconfig:
            SCRIPTNAME = os.path.basename(__file__)
            CNFG = relative_config_file([SCRIPTNAME, args.Labconfig], SCRIPTNAME)
            self.cfg = CNFG
            if args.Labconfig.startswith(Register.cloud_environment_prefix):
                os.environ["isaws"] = "yes"
        if args.Component:
            self.printer("%s | Components that are going to be \
                tested are %s." % (datetime.datetime.now(), args.Component))
            global CONFIGURATION_TO_BE_TESTED
            CONFIGURATION_TO_BE_TESTED = (self._strip_arguments(args.Component)).split(",")
        else:
            CONFIGURATION_TO_BE_TESTED = self.cfg["feature"]["stand-alone"]["config-test"]["nodes"]
        if args.logfile:
            self.logging_pad = args.logfile

    def printer(self, data, logandprint=True, noprint=True):
        """
        Routiune for customized print function.
        """
        if logandprint == False:
            print "%s" % (data)
        elif noprint == True:
            Register.logger_data.append(data)
        elif logandprint == True:
            print "%s" % (data)
            Register.logger_data.append(data)

    def save(self, data, file_name="test_configuration.log"):
        """
        Routine for saving the report.
        """
        if self.logging_pad:
            file_name = self.logging_pad
        with open(file_name, "w") as write_data:
            for line in data:
                write_data.write(line)
                write_data.write('\n')

    def call_back_test(self):
        """
        Call back routine for calling the component classes for verifying the configuration.
        """
        for component in CONFIGURATION_TO_BE_TESTED:
            self.printer("\n\t\t##############################################", noprint=False)
            self.printer("\t\t\tCURRENT TESTING COMPONENT : %s\t " % (component), noprint=False)
            self.printer("\t\t##############################################", noprint=False)
            component_lower = component.lower()
            for config_set in self.cfg[component_lower]["configurable_configs"].keys():
                Register.index = 0
                config_file = self.cfg[component_lower]\
                    ["configurable_configs"][config_set]["config_files"]
                config_type = self.cfg[component_lower]\
                    ["configurable_configs"][config_set]["config_file_type"]
                if self.cfg[component_lower]["configurable_configs"][config_set].has_key("delimit"):
                    config_delimit = self.cfg[component_lower]\
                    ["configurable_configs"][config_set]["delimit"]
                else:
                    config_delimit = None
                Register.registry[component]["file_object"] = \
                           self.get_configuration_file(self.cfg, \
                           component_lower, config_file_path=config_file, \
                           config_type=config_type, \
                           config_delimit=config_delimit)
                instance = Register.registry[component]["class_object"]()
                instance.test_configuration(cfg=self.cfg, component=component, \
                    config_set=config_set)
        return self.final_update()

    def final_update(self):
        """
        Routine for saving the report and updating the user about the improper configured hosts.
        """
        try:
            self.save(self.logger_data)
            improper_host = [failures for failures in Register.fail_tag.keys()]
            message = "Test Failed: Hosts %s are not configured per" \
                " engineering recommendations.Please refer the log" \
                " files for more information." % (improper_host)
            assert len(improper_host) == 0, "Configuration testing Failed."
            message = "Test Passed: All configurations on the cDVR tested components" \
                       " are set as per engineering recommendation."
            self.tims_dict = update_tims_data(self.tims_dict, 0, self.message, [self.test_id])

        except AssertionError as ae:
            self.tims_dict = update_tims_data(self.tims_dict, 1, self.message, [self.test_id])
        finally:
            print message
            return self.tims_dict

@Register
class PPS(StartComponentTest):

    """
    This PPS class is responsible for cheking the PPS level
    configuration and update to the call back routine.
    """

    def __init__(self):
        # This constructor is to override the base class
        # constructor to persist some of the base 
        # class's constructor values modified and to maintain
        # the value throughout the life time of this class.
        # Eg : os.environ set in constructor.
        pass

    def collate_configuration(self):
        """
        Routine for collecting the default configuration
        and the current configuration in the system.
        """
        self.configuration_that_are_configurable = self.cfg[self._lower_component]\
            ["configurable_configs"][self.config_set]["configs"]
        self.running_configuration = Register.registry[self.component]["file_object"]

    def verify_configuration(self):
        """
        Routine for verifying the collected configuration.
        """
        PPS.index += 1
        host_count = 0
        self.printer("[%s]CONFIGURATION CATEGOTY : %s:" %(PPS.index, \
            self.config_set.upper()), noprint=False)

        if self.config_set == "Generic":
            for host in self.running_configuration:
                host_count += 1
                self.printer("\t[%s] VERIFYING THE CONFIG ON THE HOST : %s."\
                    % (host_count, host), noprint=False)
                for _configuration in self.configuration_that_are_configurable:
                    space_needed = Register.length_of_column - len(_configuration)
                    # Catching if the configuration is missing from the current
                    # configuration.This could not be harm if in case its just
                    # overriding the configuration but vice-versa if it is mandatory.
                    if self.running_configuration[host].has_key(_configuration):
                        default = (DEFAULT_LOG_KEY, _configuration, \
                            self.configuration_that_are_configurable[_configuration])
                        current = (RUNNING_LOG_KEY, _configuration, \
                            self.running_configuration[host][_configuration])
                        self.printer("\t\t%s : %s => %s" % default)
                        self.printer("\t\t%s : %s => %s" % current)
                        if str(default[2]) != str(current[2]):
                            flag = "FAIL"
                            print "\t\t %s" % (_configuration), Register.alignment_type \
                                * space_needed, "...... \t [%s]" % (flag)
                            Register.fail_tag.update({host:''})
                            continue
                        flag = "OK"
                        print "\t\t %s" % (_configuration), Register.alignment_type \
                            * space_needed, "...... \t [%s]" % (flag)
                    else:
                        self.printer("\t\t%s : %s => %s" % (host, _configuration, MISSING_KEY))
                        flag = "FAIL"
                        print "\t\t %s" % (_configuration), Register.alignment_type \
                                * space_needed, "...... \t [%s]" % (flag)
                        Register.fail_tag.update({host:''})

    def test_configuration(self, cfg, component, config_set):
        """
        Entrypoint routine for the call back.
        """
        self.component = component
        self.cfg = cfg
        self.config_set = config_set
        self._lower_component = component.lower()
        self.collate_configuration()
        self.verify_configuration()

@Register
class RM(StartComponentTest):
    category_index = 0

    def __init__(self):
        # This constructor is to override the base class
        # constructor to persist some of the base
        # class's constructor values modified and to maintain
        # the value throughout the life time of this class.
        # Eg : os.environ set in constructor.
        pass

    def collate_configuration(self):
        """
        Routine for collecting the default configuration
        and the current configuration in the system.
        """
        self.config_category = []
        RM.index += 1
        self.forming_keys_for_running_configuration = {}
        #TODO: Collect the default configuration from the lab configuration.
        self.configuration_that_are_configurable = self.cfg[self.lower_component]\
                       ["configurable_configs"][self.config_set]["configs"]
        self.running_configuration = Register.registry[self.component]["file_object"]
        self.printer("[%s] CONFIGURATION CATEGOTY : %s:" % \
            (RM.index, self.config_set.upper()), noprint=False)

    def verify_configuration(self):
        """
        Routine for verifying the collected configuration.
        """
        host_count = 0
        if self.config_set == "Generic":
            for host in self.running_configuration:
                host_count += 1
                self.printer("\t[%s] VERIFYING THE CONFIG ON THE HOST : %s." % \
                    (host_count, host), noprint=False)
                for _configuration in self.configuration_that_are_configurable:
                    space_needed = Register.length_of_column - len(_configuration)
                    flag = "OK"
                    if self.running_configuration[host].has_key(_configuration):
                        default = (DEFAULT_LOG_KEY, _configuration, \
                            self.configuration_that_are_configurable[_configuration])
                        current = (RUNNING_LOG_KEY, _configuration, \
                            self.running_configuration[host][_configuration])
                        self.printer("\t\t%s : %s => %s" % default)
                        self.printer("\t\t%s : %s => %s" % current)
                        if str(default[2]) != str(current[2]):
                            flag = "FAIL"
                            print "\t\t %s" % (_configuration), Register.alignment_type *\
                                space_needed, "...... \t [%s]" % (flag)
                            Register.fail_tag.update({host:''})
                            continue
                        print "\t\t %s" % (_configuration), Register.alignment_type \
                            * space_needed, "...... \t [%s]" % (flag)
                    else:
                        print "\t\t %s" % (_configuration), Register.alignment_type \
                            * space_needed, "...... \t [%s]" % (flag)

        else:
            for config_category in self.configuration_that_are_configurable:
                self.config_category.append(config_category)

            for host in self.running_configuration:
                host_count += 1
                self.printer("\t[%s] VERIFYING THE CONFIG ON THE HOST : %s:" % \
                    (host_count, host), noprint=False)
                self.running_coreconfig = self.running_configuration[host][self.config_set]
                for category in self.config_category:
                    if self.running_coreconfig.has_key(category):
                        for header in self.configuration_that_are_configurable[category]:
                            for check_value in \
                                self.configuration_that_are_configurable[category][header]:
                                default = (DEFAULT_LOG_KEY, header, check_value, \
                                  self.configuration_that_are_configurable[category][header][check_value])
                                current = (RUNNING_LOG_KEY, header, \
                                    check_value, \
                                    self.running_coreconfig[category][header][check_value])
                                self.printer("\t\t%s : %s:%s => %s" % default)
                                self.printer("\t\t%s : %s:%s => %s" % current)
                                space_needed = Register.length_of_column - len(header)
                                if default[1] != current[1]:
                                    flag = "FAIL"
                                    print "\t\t %s" %(header), Register.alignment_type \
                                        * space_needed, "...... \t [%s]" % (flag)
                                    Register.fail_tag.update({host:''})
                                    continue
                                flag = "OK"
                                print "\t\t %s" %(header), Register.alignment_type\
                                    * space_needed, "...... \t [%s]" % (flag)

    def test_configuration(self, cfg, component, config_set):
        """
        Entrypoint routine for the call back.
        """
        self.component = component
        self.cfg = cfg
        self.config_set = config_set
        self.lower_component = component.lower()
        self.collate_configuration()
        self.verify_configuration()

@Register
class MCE(StartComponentTest):
    # Currently there are no configurable configuration avilable.
    pass

@Register
class MPE(StartComponentTest):
    # Currently there are no configurable configuration avilable.
    pass

@Register
class VMR(StartComponentTest):
    # Currently there are no configurable configuration avilable.
    pass

def doit(CNFG):
    try:
        start_time = time.time()
        set_errorlogging()
        instance = StartComponentTest()
        instance.set_arguments(CNFG)
        rc = instance.call_back_test()
        end_time = time.time()
        updatevalue = updatetimsresultsjson(CNFG, start_time, end_time, rc, 'basic-feature')
        return updatevalue
    except:
        print  "Error Occurred in Script \n"
        return (1)

if __name__ == "__main__":
    instance = StartComponentTest()
    instance.parse_arguments()
    rc = instance.call_back_test()
