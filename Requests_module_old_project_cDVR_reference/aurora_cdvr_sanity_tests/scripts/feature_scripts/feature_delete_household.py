#!/usr/bin/python

import os
import sys
from pprint import pprint
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from V3_planner import *


def _household_exists(url):
    headers = dict()
    headers["Source-Type"] = "WEB"
    headers["Source-ID"] = "127.0.0.1"
    headers["Accept"] = "application/json"
    result = False
    try:
        # r = requests.get(url, headers=headers, timeout=15, verify=False)
        r = sendURL("get", url, header=headers, server_timeout=15)
        if r.status_code == 200:
            result = True
    except Exception as e:
        result = False
    return result


def _delete_household(household_index, host, cfg):
    # set values based on config
    protocol = cfg['upm']['protocol']
    port = cfg['upm']['port']
    prefix = cfg['feature']['household_prefix']
    householdid = prefix + str(household_index)
    if "no_upm" in cfg['test-flags']:
        result = delete_planner(cfg, householdid, timeout=10)
    else:
        headers = dict()
        headers['Source-Type'] = "WEB"
        headers['Source-ID'] = "127.0.0.1"
        url = protocol + "://" + host + ":" + str(port) + "/upm/households/" + householdid

        result = True
        if _household_exists(url):
            print "delete via " + url
            try:
                r = requests.delete(url, headers=headers, timeout=15, verify=False)
                if r.status_code == 202:
                    print "server handling this asynchronously"
                    print r.headers
                    print "essentially need to loop while 202, then done"
                    print "TBD: handle later"
                    result = True
                elif r.status_code != 200:
                    print r.status_code
                    print r.headers
                    print r.content
                    result = False
                else:
                    result = True
            except:
                print "  Error: timeout "
                result = False
    return result


def doit(cfg, printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    script_name = os.path.basename(__file__)
    (test, ext) = os.path.splitext(script_name)
    print "Starting test " + test
    hosts = get_hosts_by_config_type(cfg, 'upm', printflg)
    throttle_milliseconds = cfg['feature']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25
    households_needed = cfg['feature']['households_needed']
    for index, host in enumerate(hosts):
        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0)
            if index % 4 == 0:
                print "waiting a few seconds in an effort for PVR deletion to catch up"
                time.sleep(2)  # give some time for PVRs to be deleted
        if _delete_household(index, host, cfg) is False:
            return 1

    # delete the rest using the first host
    while index + 1 < households_needed:
        index = index + 1

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0)

            if index % 4 == 0:
                print "waiting a few seconds in an effort for PVR deletion to catch up"
                time.sleep(2)  # give some time for PVRs to be deleted

        if _delete_household(index, hosts[0], cfg) is False:
            return 1

    print "waiting a few seconds in an effort for PVR deletion to catch up"
    time.sleep(4)  # give some time for PVRs to be deleted
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
