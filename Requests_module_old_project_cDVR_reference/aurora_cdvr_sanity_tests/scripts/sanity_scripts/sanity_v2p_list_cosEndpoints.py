#!/usr/bin/python

import os
import sys
import time
import requests
import mypaths
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
##########################################################################
#   List cos endpoints
##########################################################################
def doit(cfg,printflg=False):
    # announce
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    (test, ext) = os.path.splitext(scriptName)
    print "Starting test " + test
    name = (__file__.split('/'))[-1]
    I = 'Core DVR Functionality'     #rally initiatives  
    US = 'List  cos endpoints'
    TIMS_testlog = []
    TIMS_testlog = [name,I,US]
    if True:
        message = "Testcase warning :Skipping all COS PAM Node API because of authorization issue; Tosin is looking into it"
        print message
        TIMS_testlog.append(2)
        TIMS_testlog.append(message)
        return TIMS_testlog
    instance_list = []
    # set values based on config
    channel_list = []
    protocol = cfg['protocol']
    v2p_protocol =  cfg['v2p']['protocol']
    channel1 =cfg['test_channels']['GenericCh1']['ServiceId']
    channel_list.append(unicode(channel1)) 
    channel2 =cfg['test_channels']['GenericCh2']['ServiceId']
    channel_list.append(unicode(channel2)) 
    token = cfg['v2p']['api_token']
    Authorization = 'Bearer cisco:' + token  
    pam_Node = cfg['v2p']['pam_node']
    port = cfg['v2p']['api_port']
    headers = {
        'Authorization': Authorization
    }
    message_list = []
    service = 'COS'
    timeout = 2
    instance_check_counter = 0
    try:
        instance_list = Get_all_service_instances(cfg,service,timeout)
        if instance_list :
            print "service instance are successfully retrived"
        else:
            TIMS_testlog.append(1)
            TIMS_testlog.append('service instance are not successfully retrived')
            return TIMS_testlog
        printLog ("\nList of cos:"+str(instance_list),printflg)
        for instance in instance_list :
            service_check_counter = 0 
            print "Listting cos endpoints for: " , pam_Node
            url = v2p_protocol + "://" + pam_Node + ":" + str(port) + "/v2/serviceinstances/" +instance+ "/cosendpoints/"
            print "List cos endpoints via " + url
            r = sendURL ("get",url,timeout,headers)
            if r is not None :
                if ( r.status_code != 200):
                    message = "could not List cos endpoints for instance: " + instance
                    message_list.append(message) 
                    print r.status_code
                    print r.headers
                    print r.content
                    service_check_counter = service_check_counter + 1               
                else:
                    printLog("\nList  cos endpoints = " + r.content,printflg)
                    result=json.loads(r.content)
                    for val in result: 
                        if val['properties']['state'] == "enabled":
                            pass
                        else:
                             print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n" 
                             print "\nList  cos endpoints = " + r.content
                             print "\n" + "#"*20 + " DEBUG ENDED "+ "#"*20+ "\n" 
                             service_check_counter = service_check_counter + 1 
                             message = "state: " + val['properties']['state'] + " for id: " + val['id']
                             message_list.append(message)
            else:
                message = "could not List  cos endpoints for instance: "  + instance
                message_list.append(message)  
                service_check_counter = service_check_counter + 1    
            if service_check_counter == 0:
                print "state is enable for service"
                instance_check_counter = instance_check_counter + 1
        for item in message_list:
            print item
        if instance_check_counter == len(instance_list): 
            print "\nTestcase Passed: Cos endpoints were listed succesfully"
            TIMS_testlog.append(0)
            TIMS_testlog.append('List  cos endpoints was  successful ' )
            return TIMS_testlog
        else:
            print "\nTestcase failed: Cos endpoints were not listed succesfully"
            TIMS_testlog.append(1)
            TIMS_testlog.append('List  cos endpoints was not successful ' )
            return TIMS_testlog
    except:
            message = "Error occured in script: " + PrintException(True)
            print message
            TIMS_testlog.append(1)
            TIMS_testlog.append('List  cos endpoints was not successful ' + message)
            return TIMS_testlog
        
if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    #read config file 
    sa = sys.argv
    cfg = relative_config_file(sa,scriptName)
    if cfg['sanity']['print_cfg']:
         print "\nThe following configuration is being used:\n"
         pprint(cfg)
         print
    L = doit(cfg, True)
    exit(L[3] )

