#!/usr/bin/python

import os
import sys
from pprint import pprint
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from getCatalogServices import getCdvrServiceIds
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from V3_planner import *


def _create_household(household_index, host, cfg):
    """
    Internal function to do the actual creation
    :param household_index: index number used for the name of the household
    :param host: IP/hostname to send create request to
    :param cfg: configuration dictionary
    :return: True on success, else False
    """
    # set values based on config
    protocol = cfg['upm']['protocol']
    port = cfg['upm']['port']
    prefix = cfg['feature']['household_prefix']
    region = cfg['region']
    cmdcRegion = cfg['cmdcRegion']
    adZone = cfg['adZone']
    marketingTarget = cfg['marketingTarget']
    enabledServices = '"{0}"'.format('", "'.join(cfg['enabledServices']))
    householdid = prefix + str(household_index)
    check_test_flag = test_flag(cfg, "no_upm")
    if check_test_flag is True:
        result = create_planner(cfg, householdid, timeout=10)
    else:
        result = create_ahousehold(cfg, protocol, port, prefix, region, cmdcRegion, adZone, marketingTarget,
                                   householdid, enabledServices, host)

    return result


def _household_exists(url):
    headers = dict()
    headers["Source-Type"] = "WEB"
    headers["Source-ID"] = "127.0.0.1"
    headers["Accept"] = "application/json"
    result = False
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        if r.status_code == 200:
            result = True
    except Exception as e:
        result = False
    return result


def doit(cfg, printflg=False):
    """
    Create one or more households based on configuration. Checks if household
    already exists, and if so, assumes good as is.

    The doit(cfg) function is called by the main sanity script and the yaml
    parsed config is passed in as a dictionary.

    The yaml config must have the following defined:

       protocol: http   # example, could be https
       upm:
            host: <IP or hostname>
            port: <upm port to use>
            instances:    # optional
                upm1: <IP or hostname>
                upm2: <IP or hostname>
       sanity:
            allinstances: True   # or False (False if to skip those hosts defined
                                             under instances if instances block
                                             defined)
            household_prefix: <string>   # a prefix to use in household creation/references
            throttle_milliseconds: <number> # the number of milliseconds to use when waiting
            print_cfg: True  # to print the yaml configuration dictionary after load, else False (used by main)
       region: <some region id>
       cmdcRegion: <some cmdc region>  # typically the same as region
       adZone: <string>
       marketingTarget: <string>  # typically the same as adZone
       enabledServices:
            - <service1>
            - <service2>
            ...
    """
    # announce
    script_name = os.path.basename(__file__)
    (test, ext) = os.path.splitext(script_name)
    print "Starting test " + test

    # set values based on config
    households_needed = cfg['feature']['households_needed']
    hosts = get_hosts_by_config_type(cfg, 'upm', printflg)

    throttle_milliseconds = cfg['feature']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25

    for index, host in enumerate(hosts):
        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0)
            if index % 4 == 0:
                print "waiting a few seconds in an effort for PVR creation to catch up before 1st use"
                time.sleep(2)   # give some time for PVRs to be created

        if _create_household(index, host, cfg) is False:
            return 1

    # create the rest using the first host
    while index + 1 < households_needed:
        index = index + 1

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0)
            if index % 4 == 0:
                print "waiting a few seconds in an effort for PVR creation to catch up before 1st use"
                time.sleep(2)   # give some time for PVRs to be created

        if _create_household(index, hosts[0], cfg) is False:
            return 1

    print "waiting a few seconds in an effort for PVR creation to catch up before 1st use"
    time.sleep(4)   # give some time for PVRs to be created
    return 0


if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    # read config file
    sa = sys.argv
    cfg = relative_config_file(sa, scriptName)
    if cfg['feature']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
    exit(doit(cfg, True))
