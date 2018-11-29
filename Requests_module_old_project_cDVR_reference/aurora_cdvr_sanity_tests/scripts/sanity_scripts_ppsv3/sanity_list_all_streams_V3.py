#!/usr/bin/python

import os
import sys
import time
import requests
import json
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
##########################################################################
#  List All streams
##########################################################################


def doit(cfg, printflg=False):
    disable_warning()  # Method Called to suppress all warnings
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'  # rally initiatives
    US = 'List All streams'
    TIMS_testlog = []
    TIMS_testlog = [name, I, US]

    # set values based on config
    protocol = cfg['protocol']
    protocol_https = "https"
    hosts = [cfg['msr']['host']]  # ["rio.msr-scale.vdc7.vcte.com"]
    port = cfg['msr']['functional_port']
    headers = {
        'Pragma': 'no-cache',
        'Accept': 'application/json, text/plain, */*',
        'Cache-Control': 'no-cache',
        'Authorization': 'Basic bmdpbng6bmdpbng=',
        'Connection': 'keep-alive'
    }
    recording_api = cfg['recording_api']
    v2p_host = cfg['v2p']['masters']
    v2p_port = cfg['v2p']['api_port']
    v2p_protocol = cfg['v2p']['protocol']
    token_key = cfg['v2p']['api_token']
    token = "Bearer cisco:" + token_key
    headers = {'Accept': 'application/json;charset=utf-8'}
    headers_v2p = {'Authorization': token}
    timeout = 5
    any_host_pass = 0
    if recording_api == "v2p":
        for host in v2p_host:
            url = v2p_protocol + "://" + host + ":" + \
                str(v2p_port) + "/v2/channellineups"
            print "List All streams ", url
            r = sendURL("get", url, timeout, headers_v2p)
            if r is not None:
                if (r.status_code != 200):
                    print "Problem accessing: " + url
                    print r.status_code
                    print r.headers
                    print r.content
                else:
                    if r.content is None:
                        print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                        print 'List All streams' + json.dumps(json.loads(r.content), indent=4, sort_keys=False)
                        print "\n" + "#" * 20 + " DEBUG ENDED   " + "#" * 20 + "\n"
                    any_host_pass = any_host_pass + 1
                    print r.content
        if any_host_pass == len(v2p_host):
            msg = 'Testcase passed :List All streams ran successfully.'
            print msg
            TIMS_testlog.append(0)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            msg = 'Testcase failed :List All streams was not successful'
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog
    else:
        for index, host in enumerate(hosts):
            url = protocol + "://" + host + ":" + str(port) + "/api/streams"
            print "List All streams ", url
            r = sendURL("get", url, timeout, headers)
            if r is not None:
                if (r.status_code != 200):
                    print "Problem accessing: " + url
                    print r.status_code
                    print r.headers
                    print r.content
                else:
                    if r.content is None:
                        print "\n" + "#" * 20 + " DEBUG STARTED " + "#" * 20 + "\n"
                        print 'List All streams' + json.dumps(json.loads(r.content), indent=4, sort_keys=False)
                        print "\n" + "#" * 20 + " DEBUG ENDED   " + "#" * 20 + "\n"
                    any_host_pass = any_host_pass + 1
                    print r.content
        if any_host_pass:
            msg = 'Testcase passed :List All streams ran successfully.'
            print msg
            TIMS_testlog.append(0)
            TIMS_testlog.append(msg)
            return TIMS_testlog
        else:
            msg = 'Testcase failed :List All streams was not successful'
            print msg
            TIMS_testlog.append(1)
            TIMS_testlog.append(msg)
            return TIMS_testlog


if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    # read config file
    sa = sys.argv
    cfg = relative_config_file(sa, scriptName)
    if cfg['sanity']['print_cfg']:
        print "\nThe following configuration is being used:\n"
        pprint(cfg)
        print
    L = doit(cfg, True)
    exit(L[3])
