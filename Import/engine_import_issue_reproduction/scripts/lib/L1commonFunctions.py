from __future__ import division
import json
import os
import sys
from pprint import pprint
import calendar
import time
import random
import requests
import subprocess
from readYamlConfig import readYAMLConfigs
import linecache
import datetime
import warnings
import logging
import math
import inspect
from logger import enable_logging

'''
This file is a common library  of Level 1 Atomic Functions.It should  stricly  contain  functions  performing  basic/unitary actions.
Level 1 functions can be  invoked by Level 2,Level 3  and the main script.
'''

def config_info():
    frm = inspect.stack()[-2]
    cfg = frm[0].f_globals['cfg']
    return cfg
#####################################################################################################################
def disable_warning():
    warnings.filterwarnings("ignore")
####################################################################################################################
def set_errorlogging(Debug=False):
    if Debug:
        logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="a+",format="%(asctime)-15s %(levelname)-8s %(message)s")
    else:
        UseLogging = True
        if UseLogging:
            logging.basicConfig()
            logging.getLogger().setLevel(logging.ERROR)
            logging.propogate = True
#####################################################################################################################
def printLog(s,printflg):
    """
    To print the message in the console based on the flag setted
    :param s: Message to be printed
    :param printflg: print flag True will print the message False will not
    :return: None
    """
    if printflg:
        print s
    return(0)
#######################################################################################################################
def sendURL (method,url,server_timeout=None,header=None,payload_content=None):
    """
    Make the request to the API method.
    :param method:
    :param url:
    :param server_timeout:
    :param header:
    :param payload_content:
    :return:
    """

    cp_ports = [':4019', ':4059', ':443']
    if any(port in url for port in cp_ports):
        cfg = config_info()
        cert = cfg['https_certificate']
        #cert = "/home/centos/https/cdvr.dc100.com.pem"
        dir_path = os.path.abspath(__file__)
        script_dir = dir_path.split('/scripts')[0]
        #print "Script Dir :", script_dir
        cert = script_dir + "/config/"+ cfg['LABNAME'] +"/"+cert
        #print "Cert path :", cert
    else:
        cert = False


    try:
        if(method == "post"):
            r = requests.post(url, data = payload_content, headers=header, timeout=server_timeout, allow_redirects=True, verify=cert)
            return r
        elif(method == "put"):
            r = requests.put(url, data= payload_content, headers=header, timeout=server_timeout, allow_redirects=True, verify=cert)
            return r
        elif(method == "head"):
            r = requests.head(url, headers=header, timeout=server_timeout, allow_redirects=True)
            return r
        elif(method == "delete"):
            r = requests.delete(url, data= payload_content, headers=header, timeout=server_timeout, allow_redirects=True, verify=cert)
            return r
        else:
            r =requests.get(url, headers=header, timeout=server_timeout, verify=cert, allow_redirects=True)
            return r
    except requests.exceptions.RequestException as error:
        print error
        print "Problem accessing ...... " + url
    return None
#######################################################################################################################
def epochtime(duration="Null"):
    """
    To get the epoc time window for n number of hours
    :param duration:
    :return:
    """
    timeduration = duration*3600000 #Duration in hour
    if (duration !="Null"):
        startwindow = calendar.timegm(time.gmtime()) * 1000
        endwindow  = startwindow + timeduration
        epochTimewindow =str(startwindow) + "~" +str(endwindow)
    else:
        time1 = calendar.timegm(time.gmtime()) * 1000 + random.randint(0,23)*60*60*1000
        time2 = calendar.timegm(time.gmtime()) * 1000 + random.randint(0,23)*60*60*1000
        if (time1 > time2) :
            startwindow = time2
            endwindow = time1+3600000
        else:
            startwindow = time1
            endwindow = time2+3600000
        epochTimewindow =str(startwindow) + "~" + str(endwindow)
    return(epochTimewindow)
#########################################################################################################################
def isotime(duration="Null"):
    """
    To get the timewindow of n hours in ISO format %Y-%m-%dT%H:%M:%SZ
    :param duration:
    :return:
    """
    timeduration = duration*3600 #Duration in hour
    if (duration !="Null"):
        startwindow = calendar.timegm(time.gmtime())
        startiso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(startwindow))
        endwindow  = startwindow + timeduration
        endiso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(endwindow))
        isoTimewindow ="(" +startiso + "," + endiso + ")"
    else:
        time1 = calendar.timegm(time.gmtime()) + random.randint(0,23)
        time2 = calendar.timegm(time.gmtime()) + random.randint(0,23)
        if (time1 > time2) :
            startwindow = time2
            endwindow = time1+3600
        else :
            startwindow = time1
            endwindow = time2+3600
        startiso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(startwindow))
        endiso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(endwindow))
        isoTimewindow ="(" +startiso + "," + endiso + ")"
    return(isoTimewindow)
##############################################################################################
def pingIPAddress(ipaddress,printflg):

    try:
        if printflg:
            status = subprocess.call(['ping', '-q', '-c', '3', ipaddress])
            print "----------------------------------------------------------------------"
        else:
            status = subprocess.call(['ping', '-q', '-c', '3', ipaddress], stdout=open(os.devnull, 'wb'))
        if status == 0:
            return True
        else:
            return False
    except:
        print "Unable to ping IP Address"

##################################################################################################
def get_hosts_by_config_type(cfg,hostname,printflg):

  try :
       hosts = [cfg[hostname]['host']]
       try:
           cfg_type=cfg[hostname]['config_type']
           if cfg_type == "AA":
               printLog("Config Type of " + hostname + " is AA" ,printflg)
               #Sanity Allinstances check has been removed since we have the new config file of AA and MS.
               #if cfg['sanity']['allinstances'] == True and cfg[hostname].get('instances'):
               if cfg[hostname].get('instances'):
                     for k,v in cfg[hostname]['instances'].items():
                         hosts.append(v)
               return hosts
           else:
                printLog("Config Type of " + hostname + " is MS" ,printflg)
                return hosts
       except (KeyError, IndexError, TypeError, ValueError) as e:
            printLog("Config Type of " + hostname + " is MS" ,printflg)
            return hosts
  except (KeyError, IndexError, TypeError, ValueError) as e:
      print "No Host or Config Type found in config file"

###################################################################################################
def relative_path_locator(scriptDir):
    expected_dir = "/scripts/"
    index = scriptDir.find(expected_dir)
    if index < 0:
        print "unexpected directory layout"
        exit(1)
    scriptDir = scriptDir[:index+len(expected_dir)]
    # now add directories we find (excluding those with . in their name) to the sys.path so can import
    include_these_paths = []
    # os.walk provides full paths
    for x in os.walk(scriptDir):
        if x[0].find(".") < 0:
            include_these_paths.append(x[0])
#################################################################################################
def relative_config_file(sa,scriptName):
    lsa = len(sa)
    if lsa != 3  and lsa != 2:
        print "Usage: [ python ] %s <lab name> [ <ip_override.yaml> ] " % scriptName
        print "Example: [ python ] %s lwr_integration deployed_vms.yaml" % scriptName
        print "         [ python ] %s lwr_integration " % scriptName
        print "  where lwr_integration is a directory under ../config expected to contain ips.yaml"
        print "        deployed_vms.yaml is an optional yaml file of components and their hosts/ips"
        print "        similar to ips.yaml in form (see config/README file for example)"
        print
        print " the content of the 2nd arg if provided overrides the same content if present "
        print " in content of 1st arg"
        sys.exit(1)

    labName = sa[1]
    vmInfo = None
    if lsa > 2:
        vmInfo = sa[2]

    cfg = readYAMLConfigs(labName, vmInfo)
    if cfg:
          cfg['LABNAME'] = str(labName)
          cfg['EXTRACONF'] = str(vmInfo)
          cfg['GITREPO'] = ''
          cfg['GITLASTCOMMIT'] = ''
          return cfg
    else:
        print "error reading in config file "
        sys.exit(1)

####################################################################################################
def get_timedifference(inputtime,printflg):
    """
    To get the difference between the current time and given time
    :param inputtime:
    :param printflg:
    :return:
    """
    currentsystemtime = calendar.timegm(time.gmtime()) * 1000
    if currentsystemtime < inputtime:
        timedifference = (inputtime- currentsystemtime)/1000
        return timedifference
    else:
        return 1 #Return 1 second if system time is greater than input time

###################################################################################################
def PrintException(returnvalue=False):
    """
    To print the execution status of the script. It will get the exec info and print the necessary details
    :param returnvalue:
    :return:
    """
    exc_type,exc_obj,tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    exception =  'EXCEPTION IN ({0}, LINE {1} \'{2}\'): {3}'.format(filename, lineno, line.strip(), exc_obj)
    if returnvalue == True:
        return exception
    else:
        print exception
######################################################################################################################
def get_percentage(percentagevalue,inputvalue):
    """
    To get the percentage based on the input value
    :param percentagevalue:
    :param inputvalue:
    :return:
    """
    percentage = percentagevalue/100
    diskquota_percent = percentage * inputvalue
    diskquota_percent = int(diskquota_percent)
    return(diskquota_percent)
##################################################################################################################################
def change_diskQuota_value(mode,val,percent):
    """
    To  increment or decrement the diskquota based on the percentage given
    :param mode:
    :param val:
    :param percent:
    :return:
    """
    if mode=="inc":
       Increased_diskQuota_value=int(float(val)*(1+(0.01*float(percent))))
       return Increased_diskQuota_value
    elif mode=="dec":
       Decreased_diskQuota_value=int(float(val)*(1-(0.01*float(percent))))
       return Decreased_diskQuota_value
    else:
       print "Give the correct mode"
#########################################################################################################################
def epochtime_lessorgreaterthancurrenttime(duration="Null"):
    """
    To get the epoch time from -n hours to +n hours. Widely used in scripts without postime, current broadcasting programs.
    :param duration:
    :return:
    """
    timeduration = duration*3600000 #Duration in hour
    if (duration !="Null"):
        currentsystemtime = calendar.timegm(time.gmtime()) * 1000
        endwindow = currentsystemtime + timeduration
        startwindow  = currentsystemtime - timeduration
        epochTimewindow =str(startwindow) + "~" +str(endwindow)
    else:
        time1 = calendar.timegm(time.gmtime()) * 1000 + random.randint(0,23)*60*60*1000
        time2 = calendar.timegm(time.gmtime()) * 1000 + random.randint(0,23)*60*60*1000
        if (time1 > time2) :
            startwindow = time2
            endwindow = time1+3600000
        else :
            startwindow = time1
            endwindow = time2+3600000
        epochTimewindow =str(startwindow) + "~" + str(endwindow)
    return(epochTimewindow)
###################################################################################################################################
def iso2epoch(isovalue):
    """
    Convert the ISO time in "%Y-%m-%dT%H:%M:%SZ" format to EPOC time
    Widely used in Guard time test cases
    :param isovalue:
    :return:
    """
    try:
        epochvalue = calendar.timegm(datetime.datetime.strptime(isovalue, "%Y-%m-%dT%H:%M:%SZ").timetuple())
        return epochvalue
    except ValueError:
        epochvalue = calendar.timegm(datetime.datetime.strptime(isovalue, "%Y-%m-%dT%H:%M:%S.%fZ").timetuple())
        return epochvalue
    except:
        print "Error in converting iso to epoch timestamp"
        return None
###################################################################################################################################
def epoch2iso(epochvalue):
    """
    Convert the EPOC time to ISO time format %Y-%m-%dT%H:%M:%SZ
    Widely used in manual booking
    :param epochvalue:
    :return:
    """
    try:
        isovalue = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epochvalue))
        return isovalue
    except:
        print "Error in converting epoch to iso timestamp"
        return None
###################################################################################################################################
def isotimetoseconds(durationvalue):
    """
    Convert the ISO time to Seconds
    :param durationvalue:
    :return:
    """
    try:
        val = time.strptime(durationvalue, "%H:%M:%S")
        timeinseconds = datetime.timedelta(hours=val.tm_hour, minutes=val.tm_min, seconds=val.tm_sec).seconds
        return timeinseconds
    except:
        print "Error in converting iso time time to seconds"
        return None
###################################################################################################################################
def seconds2isotime(timeinseconds):
    """
    Convert the Seconds to ISO format
    Widely used in Bookmark related test cases
    :param timeinseconds:
    :return:
    """
    try:
        isovalue = time.strftime("%H:%M:%S", time.gmtime(timeinseconds))
        return isovalue
    except:
        print "Error in converting seconds to iso time"
        return None
###################################################################################################################################
def roundofftonextint(inputvalue):
    try:
        roundoffvalue = int(math.ceil(inputvalue/60))
        return roundoffvalue
    except:
        return 0
############################################################################################################
def test_flag(cfg,test_flag):
    """
    To skip the test cases based on the flags declared in config.
    Widely used to skip the timebased recording test cases
    :param cfg:
    :param test_flag:
    :return:
    """
    try:
       config_test_flag = cfg['test-flags']
       print "Test flag available....",config_test_flag
       if test_flag in config_test_flag:
           return True
       else:
           return False
    except:
        return False
########################################################################################################################
def blockPrint():
    """
    This function will disable the successive prints. Make sure
    enablePrint called after sometime to reenable back the Prints.
    """
    org = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    return org.get_file()

#########################################################################################################################
def enablePrint(filename=None):
    """
    This will enable the Prints and it will be called after
    blockPrint function call happened otherwise this function is
    of no use
    """
    sys.stdout = sys.__stdout__
    enable_logging(filename=filename, mode='a')
######################################################################################################################
