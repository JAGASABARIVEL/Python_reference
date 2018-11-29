'''
This file is a library of common reusable Level 3 Functions.It should  strictly contain functions performing a logical high level test action 
made up of complex test sub-actions 
Level 3 functions can be  invoked by the main script.
'''
import json
import os
import sys
from subprocess import Popen, PIPE
import paramiko
from paramiko import client
from readYamlConfig import readYAMLConfigs
from jsonReadWrite import JsonReadWrite
from pprint import pprint
import calendar
import requests
import random
import time
import re
import datetime
import threading
import Queue
import ast
import inspect
from itertools import chain
from multiprocessing import Process
from multiprocessing import Queue as mpq
from xml.etree import ElementTree as ET
from os.path import isfile,join
from L1commonFunctions import *
from L2commonFunctions import *

#####################################################################################################################
def get_cmdcServiceList(cfg,cmdc_host,cmdc_headers,timeout,printflg=False):
    global any_host_pass
    protocol = cfg['protocol']
    port = cfg['cmdc']['port']
    region = cfg['region']
    catalogueId = cfg['catalogueId']
    current_time = calendar.timegm(time.gmtime()) * 1000
    timewindows = epochtime(10)
    serviceids= getCdvrServiceIdsperhost(protocol,cmdc_host,port,region,timeout)
    #serviceidlist = "28506,42642"
    if not serviceids :
        print "serviceids list could not be fetched"
    else:
        serviceidlist = ','.join(serviceids)
        printLog( ( "time window selected randomly is :"+ timewindows) , printflg)
        url = protocol + "://" + cmdc_host + ":" + str(port) +"/cmdc/services/schedule/"+ timewindows + "?lang=eng&serviceList=" + serviceidlist + "&count=255&region="+ str(region) +"&catalogueId=" + str(catalogueId)
        print "cmdcServiceList fetch via URL : ", url
        r = sendURL ("get",url,timeout,cmdc_headers)
        print "State Cache Endpoints:\n"+json.dumps(json.loads(r.content),indent=4,sort_keys=False)
        if r is not None :
            if r.status_code != 200:
                print "cmdc service list could not be fetched via url %s"%url
                print r.status_code
                print r.headers
                print r.content
            else:
                pass
#####################################################################################################################
def get_contentIdlist(json_responce):
    """
    Get the List of Content Ids with the EndAvailability greater than the current time.
    :param json_responce: Response from the Grid
    :return: [content Ids]
    """
    current_time = calendar.timegm(time.gmtime()) * 1000
    contents=json.loads(json_responce.text)['services']
    contentId_list = []
    for cont in contents:
        if 'contents' in cont:
           for value in cont['contents']:
                #if value['media']:
                 if value['endAvailability'] > long(current_time):
                     contentId = value['id'] + "~" + value['instanceId']
                     contentId_list.append(contentId)
    return(contentId_list)

#####################################################################################################################
def get_contentIddict(json_responce,serviceparameterlist=[]):
    """
    Get the Content ID dictionary when BroadcastDateTime and EndAvailability is greater then current time
    and the CDVR is available
    Will return broadcastdatetime , endavailability, duration and any other service parameter if specified
    :param json_responce: Grid resonse in JSON format
    :param serviceparameterlist: specific service parameter
    :return: {contentid : [broadcastdatetime, endavailability, duration]}
    """
    contents = json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict = {}
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if value['broadcastDateTime'] > long(current_time) and value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                        contentId = value['id'] + "~" + value['instanceId']
                        contentId_Dict.setdefault(contentId,[])
                        contentStartTime = value['broadcastDateTime']
                        contentEndTime = value['endAvailability']
                        duration = contentEndTime - contentStartTime
                        contentId_Dict[contentId].append(contentStartTime)
                        contentId_Dict[contentId].append(contentEndTime)
                        contentId_Dict[contentId].append(duration)
                        if serviceparameterlist:
                            for serviceparameter in serviceparameterlist:
                                try:
                                    listparameter = value[serviceparameter]
                                    contentId_Dict[contentId].append(listparameter)
                                except:
                                    pass
                except:
                   print "Exception Occurred while getting content Dict"
                   PrintException()
                   return None 
    if not contentId_Dict:
        print "Content ID Dictionary is empty"
        return None
    else:
        return(contentId_Dict)

#####################################################################################################################
def get_contentIddict_fromchannellineup(json_responce,serviceparameterlist=[]):
    contents=json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict={}
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if "generic" in value['title']:
                        if value['broadcastDateTime'] > long(current_time) and value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                            contentId = value['id'] + "~" + value['instanceId']
                            contentId_Dict.setdefault(contentId,[])
                            #if value['broadcastDateTime'] > long(current_time) and value['endAvailability']>long(current_time):
                            contentStartTime = value['broadcastDateTime']
                            contentEndTime = value['endAvailability']
                            duration = contentEndTime - contentStartTime
                            contentId_Dict[contentId].append(contentStartTime)
                            contentId_Dict[contentId].append(contentEndTime)
                            contentId_Dict[contentId].append(duration)
                            if serviceparameterlist:
                                for serviceparameter in serviceparameterlist:
                                    listparameter = value[serviceparameter]
                                    contentId_Dict[contentId].append(listparameter)
                except:
                   print "Exception Occurred while getting content Dict"
                   PrintException()
                   return None 
    if not bool(contentId_Dict):     
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "Content ID Dictionary is empty"        
        return None
    else:
        return(contentId_Dict)
#####################################################################################################################
def get_contentIddict_lessthancurrenttime(json_responce,serviceparameterlist=[]):
    """
    Get the Content ID dictionary when BroadcastDateTime is less than the current time and
    EndAvailability is greater then current time  and the CDVR is available
    Will return broadcastdatetime , endavailability, duration and any other service parameter if specified
    :param json_responce: Grid resonse in JSON format
    :param serviceparameterlist: specific service parameter
    :return: {contentid : [broadcastdatetime, endavailability, duration]}
    """
    contents = json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict = {}
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if value['broadcastDateTime'] < long(current_time) and value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                        contentId = value['id'] + "~" + value['instanceId']
                        contentId_Dict.setdefault(contentId,[])
                        #if value['broadcastDateTime'] > long(current_time) and value['endAvailability']>long(current_time):
                        contentStartTime = value['broadcastDateTime']
                        contentEndTime = value['endAvailability']
                        duration = contentEndTime - contentStartTime
                        contentId_Dict[contentId].append(contentStartTime)
                        contentId_Dict[contentId].append(contentEndTime)
                        contentId_Dict[contentId].append(duration)
                        if serviceparameterlist:
                            for serviceparameter in serviceparameterlist:
                                listparameter = value[serviceparameter]
                                contentId_Dict[contentId].append(listparameter)
                except:
                   print "Exception Occurred while getting content Dict"
                   PrintException()
                   return None 
    if not bool(contentId_Dict):     
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "Content ID Dictionary is empty"        
        return None
    else:
        return(contentId_Dict)

##############################################################################################################################################
#Grid Request for List of Channels
##############################################################################################################################################
def fetch_gridRequest(catalogueId,protocol,host_cmdc,port_cmdc,serviceIds,region,timeout,printflg=False,timespan=2):
    """
    Get the Grid Response for an window of 2 hours from CMDC for a list of service Ids
    :param catalogueId: Catalogue to be used. Got from Config.
    :param protocol: Protocol to be used. Got from Config
    :param host_cmdc: CMDC Host. Got from config
    :param port_cmdc: CMDC PORT. Got from Config
    :param serviceIds: List of service Ids in which the content needs to be fetched
    :param region: Region number. Got from Config
    :param timeout: Time to wait for the reponse
    :param printflg: Flag for log print
    :return: JSON response if success else None
    """
    headers = {
            'Accept': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
                }
    timewindows = epochtime(timespan)
    serviceidlist = ','.join(serviceIds)
    url = protocol + "://" + host_cmdc + ":" + str(port_cmdc) +"/cmdc/services/schedule/"+ timewindows + "?lang=eng&serviceList=" + serviceidlist + "&count=255&region="+ str(region) +"&catalogueId=" + str(catalogueId)
    print "cmdcServiceList fetch via URL : ", url
    r = sendURL("get",url,timeout,headers)
    if r is not None:
        if r.status_code != 200:
            print "Grid request fetching failed via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            if r.content == "[]":
                print "Grid Service Response is empty"
                return None
            else:
                return r
    else:
        print "Not able to fetch Grid Response"
        return None

##############################################################################################################################################
def fetch_gridRequest_lessthancurrenttime(catalogueId,protocol,host_cmdc,port_cmdc,serviceIds,region,timeout,printflg=False):
    """
    Get the Grid Response for an window from -1 hour to +1 hour from current time, from CMDC for a list of service Ids
    :param catalogueId: Catalogue to be used. Got from Config.
    :param protocol: Protocol to be used. Got from Config
    :param host_cmdc: CMDC Host. Got from config
    :param port_cmdc: CMDC PORT. Got from Config
    :param serviceIds: List of service Ids in which the content needs to be fetched
    :param region: Region number. Got from Config
    :param timeout: Time to wait for the reponse
    :param printflg: Flag for log print
    :return:JSON response if success else None
    """
    headers = {
            'Accept': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
                }
    timewindows = epochtime_lessorgreaterthancurrenttime(1)
    serviceidlist = ','.join(serviceIds)
    url = protocol + "://" + host_cmdc + ":" + str(port_cmdc) +"/cmdc/services/schedule/"+ timewindows + "?lang=eng&serviceList=" + serviceidlist + "&count=255&region="+ str(region) +"&catalogueId=" + str(catalogueId)
    print "cmdcServiceList fetch via URL : ", url
    r = sendURL("get", url, timeout, headers)
    if r is not None:
        if r.status_code != 200:
            print "Grid request fetching failed via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            if r.content == "[]":
                print "Grid Service Response is empty"
                return None
            else:
                return r
    else:
        print "Not able to fetch Grid Response"
        return None

#######################################################################################################################

def do_PPSbooking(port,protocol,pps_host,householdid,pps_headers,payload,random_contentId,timeout,printflg=False):
    """
    Perform PPS booking for a Household Id with the Payload
    :param port: PPS port
    :param protocol: PPS protocol
    :param pps_host: PPS Host
    :param householdid: Household Id to book
    :param pps_headers: Default PPS headers
    :param payload: Payload with Content Id
    :param random_contentId: Content Id - for print message
    :param timeout: Timeout in seconds
    :param printflg: Flag to print the response in log
    :return: PASS if success else FAIL
    """

    url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/bookings"
    print "\nPPS booking via %s " %url
    r = sendURL("post", url, timeout, pps_headers, payload)
    if r is not None:
        if r.status_code != 201:
            print "PPS Booking Failed via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return "FAIL"
        else:
            printLog("PPS Booking successful for : %s\n" %random_contentId, printflg)
            printLog("Status Code : %s\n" %r.status_code, printflg)
            return "PASS"
    else:
        return "FAIL"

#######################################################################################################################

def do_PPSbooking_TBR(port,protocol,pps_host,householdid,pps_headers,payload,timeout,printflg=False):
    """
    Perform Time Based Booking for the start time, end time and channel mentioned in payload on the HouseholdId
    :param port: PPS port
    :param protocol: PPS protocol
    :param pps_host: PPS host
    :param householdid: HouseholdId
    :param pps_headers: Default PPS Header
    :param payload: PPS payload with starttime, endtime and channel
    :param timeout: Timeout in seconds
    :param printflg: Flag to print the response in log
    :return: PASS if booking success else FAIL
    """

    url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/bookings"
    print "\nPPS time based booking via %s " %url
    r = sendURL("post", url, timeout, pps_headers, payload)
    if r is not None:
        if r.status_code != 201:
            print "PPS Booking Failed via url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return "FAIL"
        else:
            printLog("Status Code : %s\n"%r.status_code,printflg)
            return "PASS"
    else:
        return "FAIL"

#######################################################################################################################

def delete_PPSbooking(port,protocol,pps_host,pps_headers,timeout,contentURI,printflg=False):
    """
    Delete the PPS booking of booked content using the URI from booked response
    :param port: PPS port
    :param protocol: PPS protocol
    :param pps_host: PPS host
    :param pps_headers: PPS header
    :param timeout: Timeout value in seconds
    :param contentURI: URI to delete the content
    :param printflg:Flag to print the response in log
    :return:PASS if the success else FAIL
    """
    url = protocol + "://" + pps_host + ":" + str(port) + contentURI
    print "\nDelete PPS booking via %s" %url
    r = sendURL("delete", url, timeout, pps_headers)
    if r is not None :
        if r.status_code != 200:
            print "Deletion of PPS Booking Failed via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return "FAIL"
        else:
            print "PPS Booking Deleted successfully"
            printLog("Status Code : %s\n"%r.status_code,printflg)
            return "PASS"
    else:
        return "FAIL"

#######################################################################################################################

def delete_PPSrecording(port,protocol,pps_host,pps_headers,timeout,contentURI,printflg=False):
    """
    Delete the recording content using the URI
    :param port: PPS port
    :param protocol: PPS protocol
    :param pps_host: PPS host
    :param pps_headers: PPS header
    :param timeout: Ttimeout value in seconds
    :param contentURI: URI to delete
    :param printflg:Flag to print the response in log
    :return:PASS if the success else FAIL
    """

    url = protocol + "://" + pps_host + ":" + str(port) + contentURI
    print "\nDelete PPS recording via %s " %url
    r = sendURL("delete",url,timeout,pps_headers)
    if r is not None:
        if r.status_code != 200:
            print "Deletion of PPS recording Failed via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return "FAIL"
        else:
            print "PPS recording Deleted successfully"
            printLog("Status Code : %s\n"%r.status_code,printflg)
            return "PASS"
    else:
        return "FAIL"

#####################################################################################################################################
def Get_active_service_instances(cfg,service,timeout,printflg=True):
    mos_hosts = cfg['mos']['v2url']
    msr_hosts = cfg['msr']['v2url']
    v2p_host=cfg['v2p']['pam_node']
    v2p_port=cfg['v2p']['api_port']
    v2p_protocol = cfg['v2p']['protocol']
    recording_api = cfg['recording_api']
    headers = {
        'Accept': 'application/json',
        'charset':'utf-8'
    }
    if recording_api == "v2p":
        url = v2p_protocol + "://" + v2p_host + ":" + str(v2p_port) + "/v2/serviceinstances"
    elif recording_api == "msr":
        url = msr_hosts + "/v2/serviceinstances"
    else:
        url = mos_hosts + "/v2/serviceinstances"
    print "Get Number of services via " + url
    print "Checking the service instances for "
    instance_list = []
    #print "Checking the service instances for " ,value
    r = sendURL ("get",url,timeout,headers)
    if r is not None :
         if ( r.status_code != 200):
              print "Problem accessing: " + url
              print r.status_code
              print r.headers
              print r.content
              return instance_list
         else:
              if r.content is None :
                  print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                  printLog("Get Get_active_service_instances \n" + r.content,printflg)
                  print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                  return instance_list
              result= json.loads(r.content)
              if isinstance(result,list):
                  for items in result:
                      if isinstance(items,dict):
                           if items["properties"]["state"]=="active" and (service in items["properties"]["title"]):
                               instance_list.append(items["name"])
                  return instance_list
    return instance_list


#####################################################################################################################################
def Get_all_service_instances(cfg,service,timeout,printflg=True):
    mos_hosts = cfg['mos']['v2url']
    msr_hosts = cfg['msr']['v2url']
    v2p_host=cfg['v2p']['pam_node']
    v2p_port=cfg['v2p']['api_port']
    v2p_protocol = cfg['v2p']['protocol']
    recording_api = cfg['recording_api']
    headers = {
        'Accept': 'application/json',
        'charset':'utf-8'
    }
    if recording_api == "v2p" :
        url = v2p_protocol + "://" + v2p_host + ":" + str(v2p_port) + "/v2/serviceinstances"
    elif recording_api == "msr":
        url =  msr_hosts + "/v2/serviceinstances"
    else :
        url =  mos_hosts + "/v2/serviceinstances"
    print "Get Number of services via " + url
    instance_list = []
    print "Checking the service instances for "
    r = sendURL ("get",url,timeout,headers)
    if r is not None :
         if ( r.status_code != 200):
              print "Problem accessing: " + url
              print r.status_code
              print r.headers
              print r.content
              return instance_list
         else:
              if r.content is None :
                  print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                  printLog("Get Get_all_service_instances \n" + r.content,printflg)
                  print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                  return instance_list
              result= json.loads(r.content)
              if isinstance(result,list):
                  for items in result:
                      if isinstance(items,dict):
                           if (service in items["properties"]["title"]):
                               instance_list.append(items["name"])
                  return instance_list
    return instance_list


#####################################################################################################################
def get_cos_NFR_token(cfg,timeout,host):
    auth_token = cfg['cos']['x-auth-user']
    auth_key = cfg['cos']['x-auth-key']
    headers = {
          'x-auth-user' : auth_token,
          'x-auth-key':auth_key
        }
    url = host + "/v1.0"
    print "get cos nfr token for via " + url
    r = sendURL ("get",url,timeout,headers)
    if r is not None :
       if ( r.status_code != 200):
           print "Problem accessing: " + url
           print r.status_code
           print r.headers
           print r.content
           return None
       else:
            if r.content is not None:
                return r
            else:
                 print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                 response = json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                 print "catalog response : \n\n"
                 print response
                 print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                 return None
    else:
         return None
######################################################################################################################
def get_contentId_neartocurrenttime(contentId_dict,printflg=False):
    """
    Get the content id which ends first from the content ID dictionary
    :param contentId_dict: Content id dictionary
    :param printflg: Flag to print the Log
    :return: Content ID dictionary
    """
    contentids = []
    contentendtimelist = []
    contentdict = {}
    for key,value in contentId_dict.iteritems():
        if value:
            contentid = key
            contentendtime = value[1]
            contentids.append(contentid)
            contentendtimelist.append(contentendtime)
    mincontentendtime = min(contentendtimelist)
    printLog("Least Content Start Time near to content time:\n" + str(mincontentendtime),printflg)
    randomcontentidindex = contentendtimelist.index(mincontentendtime)
    random_contentId = contentids[randomcontentidindex]
    printLog("Content Id corresponding to that index:\n"+random_contentId,printflg)
    if contentId_dict.has_key(random_contentId):
        contentdict.setdefault(random_contentId,[])
        contentdict[random_contentId].extend(contentId_dict.get(random_contentId))
    printLog("Content Id with the required parameters\n" +str(contentdict),printflg)
    if not contentdict:
        print "Content ID Dictionary is empty"
        return None
    else:
        return contentdict
#####################################################################################################################
def get_contentId_lessthancurrenttime(contentId_dict,printflg=False):
    """
    Get the content Id which is having least Content Broadcast time from Content Id Dictionary
    :param contentId_dict: Content id dictionary
    :param printflg: Flag to print the Log in console
    :return: Content ID Dictionary
    """
    contentids = []
    contentstarttimelist = []
    contentdict = {}
    for key,value in contentId_dict.iteritems():
       contentid = key
       contentids.append(contentid)
       contentstarttime = value[0]
       contentstarttimelist.append(contentstarttime)
    print contentstarttimelist
    mincontentstarttime = min(contentstarttimelist)
    printLog("Content Start Time lesser than required time difference:\n" + str(mincontentstarttime),printflg)
    randomcontentidindex = contentstarttimelist.index(mincontentstarttime)
    random_contentId = contentids[randomcontentidindex]
    printLog("Content Id corresponding to that index:\n"+random_contentId,printflg)
    if contentId_dict.has_key(random_contentId):
        contentdict.setdefault(random_contentId,[])
        contentdict[random_contentId].extend(contentId_dict.get(random_contentId))
    printLog("Content Id with the required parameters\n" +str(contentdict),printflg)
    if contentdict == "{}":
        print "Content ID Dictionary is empty"
        return None
    else:
        return contentdict
######################################################################################################################
def get_contentIdlist_allcontentiddict_channellineup(contentId_dict,printflg=False):
    contentids = []
    contentstarttimelist = []
    sortedcontentstarttimelist = []
    mincontentstarttimelist = []
    randomcontentIdlist = []
    finalcontentidlist = []
    for key,value in contentId_dict.iteritems():
        if value:
            contentid = key
            contentstarttime = value[0]
            contentids.append(contentid)
            contentstarttimelist.append(contentstarttime)
    sortedcontentstarttimelist = sorted(contentstarttimelist)
    for mincontentstarttime in sortedcontentstarttimelist:
        if mincontentstarttime not in mincontentstarttimelist:
            mincontentstarttimelist.append(mincontentstarttime)
    for mincontentstarttime in mincontentstarttimelist:
        printLog("\nLeast Content Start Time near to content time: " + str(mincontentstarttime),printflg)
        randomcontentidindex = contentstarttimelist.index(mincontentstarttime)
        random_contentId = contentids[randomcontentidindex]
        printLog("Content Id corresponding to that index:\n"+random_contentId,printflg)
        randomcontentIdlist.append(random_contentId)
    for random_contentId in randomcontentIdlist:
        for key,value in contentId_dict.iteritems():
            if random_contentId in key:
                finalcontentidlist.append((key,value[0],value[1],value[2]))
    sortedcontentidlist = sorted(finalcontentidlist,key=lambda element:element[1])
    printLog("Content Id with the required parameters\n" +str(sortedcontentidlist),printflg)
    if not sortedcontentidlist:
        print "Content ID List is empty"
        return None
    else:
        return sortedcontentidlist

######################################################################################################################
def get_contentId_greaterthan_currenttime(contentId_dict,timedifference,printflg=False):
    """
    Get the content id which start first from the content ID dictionary, after timedifference specified
    :param contentId_dict:
    :param timedifference:
    :param printflg:
    :return:
    """

    contentids = []
    contentstarttimelist = []
    contentdict = {}
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentIdStartTimerequired = current_time + (timedifference*60*1000) #timedifference in minutes
    for key,value in contentId_dict.iteritems():
       if value[0] > contentIdStartTimerequired:
           contentid = key
           contentids.append(contentid)
           contentstarttime = value[0]
           contentstarttimelist.append(contentstarttime)
    mincontentstarttime = min(contentstarttimelist)
    printLog("Content Start Time greater than required time difference:\n" + str(mincontentstarttime),printflg)
    randomcontentidindex = contentstarttimelist.index(mincontentstarttime)
    random_contentId = contentids[randomcontentidindex]
    printLog("Content Id corresponding to that index:\n"+random_contentId,printflg)
    if contentId_dict.has_key(random_contentId):
        contentdict.setdefault(random_contentId,[])
        contentdict[random_contentId].extend(contentId_dict.get(random_contentId))
    printLog("Content Id with the required parameters\n" +str(contentdict),printflg)
    if not contentdict:
        print "Content ID Dictionary is empty"
        return None
    else:
        return contentdict

######################################################################################################################
def get_contentId_fromcontentIddictall(contentId_dict,printflg=False):
    """
    ** DEPRICATED **
    Get the content id which start first from the content ID dictionary.
    :param contentId_dict:
    :param printflg:
    :return:
    """
    contentids = []
    contentstarttimelist = []
    contentdict = {}
    for key,value in contentId_dict.iteritems():
       contentid = key
       contentids.append(contentid)
       contentstarttime = value[0]
       contentstarttimelist.append(contentstarttime)
    mincontentstarttime = min(contentstarttimelist)
    printLog("Content Start Time lesser than required time difference:\n" + str(mincontentstarttime),printflg)
    randomcontentidindex = contentstarttimelist.index(mincontentstarttime)
    random_contentId = contentids[randomcontentidindex]
    printLog("Content Id corresponding to that index:\n"+random_contentId,printflg)
    if contentId_dict.has_key(random_contentId):
        contentdict.setdefault(random_contentId,[])
        contentdict[random_contentId].extend(contentId_dict.get(random_contentId))
    printLog("Content Id with the required parameters\n" +str(contentdict),printflg)
    if contentdict == "{}":
        print "Content ID Dictionary is empty"
        return None
    else:
        return contentdict
######################################################################################################################
def get_overlappingcontentIds_fromcontentIddictall(contentId_dict,printflg=False):
    """
    Get the content id dict with the contents which are overlapping with other content
    :param contentId_dict:
    :param printflg:
    :return:
    """
    contentids = []
    contentendtimelist = []
    contentstarttimelist = []
    contentdict = {}
    overlappingcontentidlist = []
    finalcontentidlist = []
    sortedcontentidlist = []
    for key,value in contentId_dict.iteritems():
       contentid = key
       contentids.append(contentid)
       contentstarttime = value[0]
       contentendtime = value[1]
       contentstarttimelist.append(contentstarttime)
       contentendtimelist.append(contentendtime)
    mincontentstarttime = min(contentstarttimelist)
    mincontentendtime = min(contentendtimelist)
    for key,value in contentId_dict.iteritems():
        if value[1] >= mincontentendtime and value[0] < mincontentendtime:
            print key,value
            overlappingcontentidlist.append(key)                       
    for random_contentId in overlappingcontentidlist:
        for key,value in contentId_dict.iteritems():
            if random_contentId in key:
                finalcontentidlist.append((key,value[0],value[1],value[2])) 
    sortedcontentidlist = sorted(finalcontentidlist,key=lambda element:element[1])
    #printLog("Content Id with the required parameters\n" +str(contentdict),printflg)
    if sortedcontentidlist == "[]":
        print "Content ID list is empty"
        return None
    else:
        return sortedcontentidlist

#######################################################################################################################
def check_state_basedoncontentId(inputjsonresponse,inputcontentId,checkfirststate,checksecondstate=None,printflg=False):
    """
    ** DEPRICEATED **
    Check if the specified content is in the specified state or the seconds specified state.
    :param inputjsonresponse:
    :param inputcontentId:
    :param checkfirststate:
    :param checksecondstate:
    :param printflg:
    :return:
    """
    try:
        jsoncontent = json.loads(inputjsonresponse.content)
        printLog("Json Content Response:\n"+json.dumps(json.loads(inputjsonresponse.content),indent=4,sort_keys=False),printflg)
        if isinstance(jsoncontent,list):
            for items in jsoncontent:
                if checksecondstate:
                    if items['state'] == checkfirststate or items['state'] == checksecondstate and items['scheduleInstance'] == inputcontentId:
                        return "PASS"
                    else:
                        return "FAIL"
                else:
                    if items['state'] == checkfirststate and items['scheduleInstance'] == inputcontentId:
                        return "PASS"
                    else:
                        return "FAIL"
    except:
        PrintException()

###########################################################################################################################
def get_itemsfromjsonresponse(inputjsonresponse,parameterlist=[],printflg=False):
    """
    ** DERICATED **

    :param inputjsonresponse:
    :param parameterlist:
    :param printflg:
    :return:
    """
    try:
        returnparameterlist = []
        jsoncontent = json.loads(inputjsonresponse.content)
        for items in jsoncontent:
            for parameter in parameterlist:
                try:
                    returnvalue = items[parameter]
                    returnparameterlist.append(returnvalue)
                except KeyError:
                    returnvalue = items['content'][parameter]
                    returnparameterlist.append(returnvalue)
                    continue
        return (returnparameterlist)
    except:
       PrintException()

###########################################################################################################################
def setup_smsession(protocol,smhost,smport,inputcontentid,inputdeviceId,timeout,printflg=False):

    try:

        print inputcontentid
        print inputdeviceId
        url = protocol + "://" + smhost + ":" + str(smport) + "/sm/streamingSession"
        print "Setup the Session for the Playback of Recording via" + url
        sm_headers = {
            'Content-Type': 'application/json'
            }
        payload = """{
            "contentIdType" : "URL",
            "contentId" : "%s",
            "contentType" : "CDVR",
            "deviceId" : "%s",
            "isManaged": true,
            "catalogueId" : "2"
            }"""%(inputcontentid,inputdeviceId)
        r = sendURL ("post",url,timeout,sm_headers,payload)
        if r is not None :
            if r.status_code != 200:
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                if r.content == "{}":
                    print "SM Session Response is empty"
                    return None
                else:
                    return r
        else:
            print "Not able to get the SM Session Response"
            return None
    except:
        PrintException()
        return None

###########################################################################################################################
def get_responsebyURL(url,timeout):
    """
    ** DEPRICATED **
    Make a get request and return the response
    :param url:
    :param timeout:
    :return:
    """
    try:
        headers = {
            'Content-Type':'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }

        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if r.status_code != 200:
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
            else:
                return r
    except:
        PrintException()
########################################################################################################################################
def fetch_booking_library(cfg,protocol,pps_host,port_pps,householdid,timeout,pps_headers,printflg=False):
    """
    Get the booking catalog of a household from PPS
    :param cfg:
    :param protocol:
    :param pps_host:
    :param port_pps:
    :param householdid:
    :param timeout:
    :param pps_headers:
    :param printflg:
    :return:
    """

    url = protocol + "://"+ pps_host + ":" + str(port_pps) +"/pps/households/"+ str(householdid) +"/bookings"
    r = sendURL ("get",url,timeout,pps_headers)
    print "Booked library fetched  via URL : ", url
    if r is not None :
        if r.status_code != 200:
            print "Booked library fetch via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return r
        else:
            if r.content == "[]": 
                print "Booked Library is empty"
                return None
            else:
                return r
########################################################################################################################################
def fetch_recorded_library(cfg,protocol,pps_host,port_pps,householdid,timeout,printflg=False):
    """
    Get the recorded catalog of a household from PPS
    :param cfg:
    :param protocol:
    :param pps_host:
    :param port_pps:
    :param householdid:
    :param timeout:
    :param printflg:
    :return:
    """
    headers = {
                    'Content-Type': 'application/json',
                    'Source-Type': 'WEB',
                    'Source-ID': '127.0.0.1',
                     }
    url = protocol + "://"+ pps_host + ":" + str(port_pps) +"/pps/households/"+ str(householdid) +"/recordings"
    r = sendURL ("get",url,timeout,headers)
    print "Recorded library fetched  via URL : ", url
    if r is not None :
        if r.status_code != 200:
            print "Recorded library fetch via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return r
        else:
            if r.content == "[]":
                print "Recorded Library is empty"
                return None
            else:
                return(r)
##############################################################################################################################################
def get_seriesId(grid_response):
    """
    ** DEPRICATED **
    Get the content id of the series from the json response
    :param grid_response:
    :return:
    """
    contents = json.loads(grid_response.content)['services']
    seriesId_list = []
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                   try :
                        if value['seriesId'] :
                            contentId = value['id'] + "~" + value['instanceId']
                            seriesId_list.append(contentId)
                   except (KeyError, TypeError, ValueError, IndexError) :
                       pass
    return(seriesId_list)
#############################################################################################################################################
def isBooked(json_response):
    """
    ** DEPRICATED **
    :param json_response:
    :return:
    """
    json_response = json.loads(json_response.content)
    if isinstance(json_response,list):
        for val in json_response:
            if val['state'] == "BOOKED":
                return("PASS")
            else:
                return("FAIL")
#############################################################################################################################################
def isRecorded(json_response):
    """
    ** DEPRICATED **
    :param json_response:
    :return:
    """
    json_response = json.loads(json_response.content)
    if isinstance(json_response,list):
        for val in json_response:
            if val['state'] == "RECORDED":
                return("PASS")
            else:
                return("FAIL")
#############################################################################################################################################
def isRecording(json_response):
    """
    ** DEPRICATED **
    :param json_response:
    :return:
    """
    json_response = json.loads(json_response.content)
    if isinstance(json_response,list):
        for val in json_response:
            if val['state'] =="RECORDING":
                return("PASS")
            else:
                return("FAIL")
#############################################################################################################################################
def isPlayable(json_response):
    """
    ** DEPRICATED **
    :param json_response:
    :return:
    """
    json_response = json.loads(json_response.content)
    if isinstance(json_response,list):
        for val in json_response:
            if val["content"]["isPlayable"] == True:
                return("PASS")
            else:
                return("FAIL")
#############################################################################################################################################
def bookedpgm_storage(json_response):
    """
    ** DUPLICATE **
    Returns the free disk space of the household.
    :param json_response:
    :return:
    """
    json_response = json.loads(json_response.content)
    return(json_response.get('freeDiskSpace'))
#############################################################################################################################################
def _household_exists(url):
    """
    To check if the household exist or not
    :param url:
    :return:
    """

    headers = {
        'Source-Type' : 'WEB',
        'Source-ID'   : '127.0.0.1',
        'Accept'      : 'application/json',
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            result = True
        else:
            result = False
    except:
        result = False
    return result

##############################################################################################################################################
def delete_household(protocol,port_upm,householdid,upm_host):
    """
    Delete the household
    :param protocol:
    :param port_upm:
    :param householdid:
    :param upm_host:
    :return:
    """
    headers = {
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
    }
    url = protocol + "://" + upm_host + ":" + str(port_upm) + "/upm/households/" + householdid
    print "Household deleted via " + url
    try:
        r = requests.delete(url, headers=headers, timeout=15)
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
###############################################################################################################################################
def setCdvrSubscriptionOffers(cfg, householdid):
        """
        Set the CDVR subscription offer for a household
        :param cfg:
        :param householdid:
        :return:
        """

        offers = getCdvrSubscriptionOffers(cfg)
        if offers == None:
            return False

        # set values based on config
        #prefix = cfg['corner']['household_prefix']
        protocol = cfg['protocol']
        hosts = [cfg['upm']['host']]
        if cfg['corner']['allinstances'] == True and cfg['upm'].get('instances'):
            for k, v in cfg['upm']['instances'].items():
                hosts.append(v)

        port = str(cfg['upm']['port'])

        households_needed = cfg['corner']['households_needed']
        throttle_milliseconds = cfg['corner']['throttle_milliseconds']
        if throttle_milliseconds < 1:
            throttle_milliseconds = 25

        headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
        }

        # pprint(hosts)

        #cdvrServiceIds = getCdvrServiceIds(cfg)

        #serviceIdsCsv = ",".join(cdvrServiceIds)

        for host in hosts:
            for index in range(households_needed):
                if index > 1:
                    time.sleep(throttle_milliseconds / 1000.0)
            for offerid in offers:
                payload = """
                {
                    "authorizationId": "%s",
                    "authorizationType": "SUBSCRIPTION"
                }
                """ % offerid
                url = protocol + "://" + host + ":" + port + "/upm/households/" + householdid + "/authorizations/subscriptions/" + str(offerid)
                print url
                r = requests.put(url, headers=headers, data=payload)
                if r.status_code != 201 and r.status_code != 200:
                    print "Problem accessing: " + url
                    print r.status_code
                    print r.headers
                    print r.content
                    return False
        return True

##############################################################################################################################################
def getCdvrSubscriptionOffers(cfg):
    """
    Get the CDVR services offers
    :param cfg:
    :return:
    """
    # set values based on config
    protocol = cfg['protocol']
    hosts = [cfg['cmdc']['host']]
    if cfg['sanity']['allinstances'] == True and cfg['cmdc'].get('instances'):
        for k,v in cfg['cmdc']['instances'].items():
            hosts.append(v)

    port = str(cfg['cmdc']['port'])
    catalogueId = str(cfg['catalogueId'])
    caSystemId = str(cfg['caSystemId'])

    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25

    #pprint(hosts)

    cdvrServiceIds = getCdvrServiceIds(cfg)

    serviceIdsCsv = ",".join(cdvrServiceIds)
    print serviceIdsCsv
    for index, host in enumerate(hosts):

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )
        url = protocol + "://" + host + ":" + port + "/cmdc/service/" + serviceIdsCsv + "/offers?catalogueId=" + catalogueId + "&caSystemId=" + caSystemId + "&count=255"

        r = requests.get(url)
        if r.status_code != 200:
            print "Problem accessing: " + url
            print r.status_code
            print r.headers
            print r.content
            return(None)

    # obviously only care about the last cmdc service retrieval (hope that's ok!)
    cdvrOffers = []
    try:
        offers = json.loads(r.text)['offers']
        for offer in offers:
            if offer['type'] == "subscription":
                cdvrOffers.append( offer['id'] )
            #print service['cdvrAvailable']
    except:
        print " failed to get offers from cmdc"
        return(None)
    return(cdvrOffers)
############################################################################################################################################
def getCdvrServiceIds(cfg):
    """
    Get all Channel IDs / Service ID  based on region
    :param cfg:
    :return:
    """

    # set values based on config
    protocol = cfg['protocol']
    hosts = [cfg['cmdc']['host']]
    if cfg['sanity']['allinstances'] == True and cfg['cmdc'].get('instances'):
        for k,v in cfg['cmdc']['instances'].items():
            hosts.append(v)

    port = cfg['cmdc']['port']
    region = cfg['region']
    cmdcRegion = cfg['cmdcRegion']

    throttle_milliseconds = cfg['sanity']['throttle_milliseconds']
    if throttle_milliseconds < 1:
        throttle_milliseconds = 25

    #pprint(hosts)

    for index, host in enumerate(hosts):

        if index > 1:
            time.sleep(throttle_milliseconds / 1000.0 )

        url = protocol + "://" + host + ":" + str(port) + "/cmdc/services/?region=" + str(region) + "&count=23"

        r = requests.get(url)
        if r.status_code != 200:
            print "Problem accessing: " + url
            print r.status_code
            print r.headers
            print r.content
            return(None)

    # obviously only care about the last cmdc service retrieval (hope that's ok!)
    cdvrServices = []
    cdvrServices1 = []
    try:
        services = json.loads(r.text)['services']
        for service in services:
            if service['cdvrAvailable'] == True:
                cdvrServices.append( service['id'] )
            #print service['cdvrAvailable']
    except:
        print " failed to get services with cdvr flag set "
        return(None)
    #cdvrServices1 = "28506,42642"
    return(cdvrServices)
#############################################################################################################################################
def get_videoplaybackurl(filename,url):

    pattern = re.compile("^[0-9\w\W]+."+"m3u8$")
    videotsurl = get_url(filename,pattern,url)
    if videotsurl :
        videots_link = requests.get(videotsurl.strip())
        tempfile = 'temp1'
        with open(tempfile, 'wb') as f:
            for chunk in videots_link.iter_content(chunk_size = 1024):
                if chunk: # filter out keep-alive new chunks
                     f.write(chunk)
            f.close()

        pattern  = re.compile("^[\w\W]+/\w+.ts$")
        videourl = get_url(tempfile,pattern,url)
        if videourl : 
            return videourl.strip()
        else:
             return None
    else :
         return None

################################################################################################################################
def get_url(filename,pattern,url):
    value = None
    for i,line in enumerate(open(filename)):
        for match in re.finditer(pattern,line):
            if line:
                value = line
                break
        else:
           continue
        break

    spliturl = url.split('/')[0:-1]
    if value : 
        videourl = '/'.join(spliturl) + "/" + value
        return videourl
    else:
        print "unable to get videourl"
        return None
###############################################################################################################################################
def check_event_recorded(contentId,recorded_lib):
    """
    Check if the content is in recorded state
    :param contentId:
    :param recorded_lib:
    :return:
    """
    recorded_lib=json.loads(recorded_lib.content)
    if recorded_lib:
        if isinstance(recorded_lib,list):
            for val in recorded_lib:
                if val['scheduleInstance'] == contentId and val["state"] == "RECORDED":
                    uri_delete = val['uri']
                    print val['title']
                    print val['recordingId']
                    return("PASS",uri_delete)
                else:
                    return("FAIL")
        else:
            return("FAIL")
    else:
        return("FAIL")
##############################################################################################################################################
def get_series_contentIddict(json_responce,serviceparameterlist=[]):
    """
    Get the future series contentd id dictionary from the JSON response
    :param json_responce:
    :param serviceparameterlist:
    :return:
    """
    contents=json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict={}
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if value['seriesId'] :
                        if value['broadcastDateTime'] > long(current_time) and value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                            contentId = value['id'] + "~" + value['instanceId']
                            contentId_Dict.setdefault(contentId,[])
                            #if value['broadcastDateTime'] > long(current_time) and value['endAvailability']>long(current_time):
                            contentStartTime = value['broadcastDateTime']
                            contentEndTime = value['endAvailability']
                            contentId_Dict[contentId].append(contentStartTime)
                            contentId_Dict[contentId].append(contentEndTime)
                            if serviceparameterlist:
                                for serviceparameter in serviceparameterlist:
                                    listparameter = value[serviceparameter]
                                    contentId_Dict[contentId].append(listparameter)
                except:
                   pass
    print contentId_Dict
    return(contentId_Dict)
##############################################################################################################################################
def check_event_booked(event_state,random_contentId,printflg=False):
    """
    Check if the event is in Booked state.

    :param event_state:
    :param random_contentId:
    :param printflg:
    :return: PASS , Duration + 120, recording id, uri, starttime, Duration
    """
    event_state = json.loads(event_state.content)
    if isinstance(event_state,list):
        for val in event_state:
 
            if val["contentId"] == random_contentId and val["state"] == "BOOKED":
                printLog("Program title " + val["title"] + "\nProgram state " + val["state"] + "\nProgram recordingId " + val["recordingId"] +"\nProgram Recurrence is " + val["recurrence"],printflg)
                booking_recordingId = val['recordingId']
                uri_delete = val['uri']
                pgm_end_time = val['content']['endAvailability']
                currentsystemtime = calendar.timegm(time.gmtime()) * 1000
                pgm_start_wait_time= (val['content']["broadcastDateTime"] - currentsystemtime)/1000
                pgm_compleetetime = (pgm_end_time -val['content']["broadcastDateTime"])/1000
                wait_time = (pgm_start_wait_time + pgm_compleetetime) + 120
                return("PASS",wait_time,booking_recordingId,uri_delete,pgm_start_wait_time,pgm_compleetetime)
            else:
                return("FAIL")
    else:
        return("FAIL")
##############################################################################################################################################
def fetch_full_details_diskquota(protocol,upm_host,port_upm,householdid,timeout,printflg=False):
    """
    Get the Disk quota of the particular household
    :param protocol:
    :param upm_host:
    :param port_upm:
    :param householdid:
    :param timeout:
    :param printflg:
    :return:
    """
    headers = {
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
        'Accept': 'text/plain',
        }
    url = protocol + "://"+ upm_host + ":" + str(port_upm) +"/upm/households/"+ str(householdid) +"/diskQuota"
    r = sendURL ("get",url,timeout,headers)
    print "Retrieve Total diskQuota fetched  via URL : ", url
    if r is not None :
        if r.status_code != 200:
            print "Retrieving Total diskQuota fetched  Failed" 
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            if r.content == "":
                print "Full diskquota details is empty"
                return None
            else:
                print "Diskquota for the household is " + str(r.content)
                return(r)
    else:
        print "Not able to fetch full details of diskquota"
        return None
#############################################################################################################################################
def fetch_diskspace_left(protocol,pps_host,port_pps,householdid,timeout,printflg=False):

    headers = {
                    'Content-Type': 'application/json',
                    'Source-Type': 'WEB',
                    'Source-ID': '127.0.0.1',
                     }
    url = protocol + "://"+ pps_host + ":" + str(port_pps) +"/pps/households/"+ str(householdid) +"/pvrs/nPVR"

    r = sendURL ("get",url,timeout,headers)
    print "Remaining diskspace left is fetched  via URL : ", url
    if r is not None :
        if r.status_code != 200:
            print "Remaining diskspace left fetching Failed"
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            if r.content == "":
                print "Diskspace left is empty"
                return None
            else:
                return(r)
    else:
        print "Not able to fetch the remaining diskspace"
        return None
#############################################################################################################################################
def bookedpgm_storage(json_response):
    """
        Returns the free disk space of the household.
        :param json_response:
        :return:
    """
    try:
        json_response = json.loads(json_response.content)
        return(json_response.get('freeDiskSpace'))
    except:
        print "Exception Occured"
        PrintException()
        return None
#############################################################################################################################################
def create_ahousehold(cfg,protocol,port_upm,prefix,region,cmdcRegion,adZone,marketingTarget,householdid,enabledServices,upm_host):
    """
    Create a household with the household id and with the enabledservices specified
    :param cfg:
    :param protocol:
    :param port_upm:
    :param prefix:
    :param region:
    :param cmdcRegion:
    :param adZone:
    :param marketingTarget:
    :param householdid:
    :param enabledServices:
    :param upm_host:
    :return:
    """
    recorderRegion = cfg['recorderRegion']
    payload = """
    {
      "householdId" : "%s",
      "householdStatus" : "ACTIVATED",
      "operateStatus": "ACTIVE",
      "locale" : {
            "region" : "%s",
            "cmdcRegion":"%s",
            "adZone": "%s",
                "marketingTarget": "%s",
                "recorderRegion": "%s"
                 },
    "enabledServices" : [%s],
    "cDvrPvr": true
    }
    """ % (householdid, region, cmdcRegion, adZone, marketingTarget, recorderRegion,enabledServices)
    headers = {
        'Content-Type': 'application/json',
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
    }
    url = protocol + "://" + upm_host + ":" + str(port_upm) + "/upm/households/" + householdid

    if _household_exists(url):
        print "Household already present: " + url
        result = True
    else:
        print "Create household via " + url
        r = requests.put(url, data=payload, headers=headers, timeout=10)
        if r.status_code != 201:
            print r.status_code
            print r.headers
            print r.content
            result = False
        else:
            result = True
    return result

##############################################################################################################################################
def _household_exists(url):
    """
    ** DUPLICATE **
    Check if the household exist
    :param url:
    :return:
    """
    headers = {
        'Source-Type' : 'WEB',
        'Source-ID'   : '127.0.0.1',
        'Accept'      : 'application/json',
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            result = True
        else:
            result = False
    except:
        result = False
    return result

##############################################################################################################################################
def delete_household(protocol,port_upm,householdid,upm_host):
    """
    Delete the household specified
    :param protocol:
    :param port_upm:
    :param householdid:
    :param upm_host:
    :return:
    """
    headers = {
        'Source-Type': 'WEB',
        'Source-ID': '127.0.0.1',
    }
    url = protocol + "://" + upm_host + ":" + str(port_upm) + "/upm/households/" + householdid
    print "Household deleted via " + url
    try:
        r = requests.delete(url, headers=headers, timeout=15)
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
#######################################################################################################################################################################################################################################################
def modify_diskQuota(cfg,protocol,upm_host,port_upm,householdid,diskquota,diskquota_headers_hh,timeout,printflg=False):
    """
    Modify the disk space <disk quota> as specified for a household
    :param cfg:
    :param protocol:
    :param upm_host:
    :param port_upm:
    :param householdid:
    :param diskquota:
    :param diskquota_headers_hh:
    :param timeout:
    :param printflg:
    :return:
    """
    url = protocol + "://"+ upm_host + ":" + str(port_upm) +"/upm/households/"+ str(householdid) +"/diskQuota"
    r = sendURL ("put",url,timeout,diskquota_headers_hh,diskquota)
    print "DiskQuota is modified  via URL : ", url
    if r is not None :
        if r.status_code != 200:
            print "DiskQuota  modification failed  via URL %s"%url
            print r.status_code
            print r.headers
            print r.content
            return("FAIL")
        else:
            return("PASS")

#######################################################################################################
def get_contentplaybackurl_withPRM(protocol,sm_host,sm_port,contentplayuri,deviceid,timeout,printflg=False):
    try:
        contenturlsessionlist = []
        #Setup the SM Session by using the contentplaybackURI and deviceid
        setupsmsessionresponse = setup_smsession(protocol,sm_host,sm_port,contentplayuri,deviceid,timeout,printflg)
        printLog("Setup SM Session Response:\n"+ json.dumps(json.loads(setupsmsessionresponse.content),indent=4,sort_keys=False),printflg)

        #Get the contentplaybackURL from the SM Session
        jsonsessionresponse = json.loads(setupsmsessionresponse.content)
        smsessionId = jsonsessionresponse['streamingSession']['smSessionId']
        contenturlsessionlist.append(smsessionId)
        contentplaybackURL = jsonsessionresponse['streamingSession']['playbackURL']
        contenturlsessionlist.append(contentplaybackURL)
        
        #return the URL and smsessionid
        if not contenturlsessionlist:
            print "Content Playback URL List is empty"
            return None
        else:
            return contenturlsessionlist
    except:
        print "Problem in getting the contentplayback URL"
        PrintException()
        return None

#################################################################################################################
def get_contentURL_withPRM(protocol,playback_host,playback_port,playback_url,contentplaybackURL,printflg=False):
    try:
        contentplaybackurlsplit = contentplaybackURL.split("/")
        contentURL = protocol + "://" +  playback_host + ":" + str(playback_port) + playback_url + contentplaybackurlsplit[4] + "/" + contentplaybackurlsplit[5]
        return contentURL
    except:
        print "Problem in getting content URL"
        PrintException()
        return None
#################################################################################################################
def get_contentID_withoutPRM(protocol,rm_host,contentplayuri,timeout,pps_headers,printflg=False):
    """

    Get the content id from RM by passing the contentplayuri

    This function is used when the PRM flag is set to False

    :param protocol:
    :param rm_host:
    :param contentplayuri:
    :param timeout:
    :param pps_headers:
    :param printflg:
    :return:
    """

    try:
        #Get the Schedule ID from the conteplayuri of the recorded event
        contenturi = contentplayuri.split("=")
        contenturijoin = contenturi[1].split("&")
        scheduleId = contenturijoin[0]

        #Get the Content ID using RM CNS Response using the above Schedule ID
        url = protocol + "://" + rm_host + "/recordingInfo/" + scheduleId + "?contentType=MPEG4&mode=playback&responseFormat=json"
        print "URL to get the RM response :",url
        getrmresponse = sendURL("get",url,timeout,pps_headers)
        if getrmresponse is not None:
            if getrmresponse.status_code == 200:
                printLog("rm response:\n" + json.dumps(json.loads(getrmresponse.content),indent = 4, sort_keys = False),printflg)
                loadrmresponse = json.loads(getrmresponse.content)
                contentId = loadrmresponse["playlist"]["segment"][0]["contentId"]
                if 'regionId' in loadrmresponse["playlist"]["segment"][0]:
                    regionid = loadrmresponse["playlist"]["segment"][0]["regionId"]
                    if regionid == "":
                        print "RegionId in RM Response is empty"
                        return None
                else:
                    print "RegionId parameter is missing in the RM Response"
                    return None

                if contentId == "":
                    print "ContentId in RM Reponse is empty"
                    return None
                else:
                    return contentId
            else:
                print "Not able to get contentID because of RM Response failure"
                print getrmresponse.status_code
                print getrmresponse.headers
                print getrmresponse.content
                return None
        else:
            print "Not able to fetch RM Response"
            return None
    except:
        print "Problem in getting content ID from RM Reposne"
        PrintException()
        return None

#################################################################################################################
def get_contentplaybacktime_withoutPRM(protocol,rm_host,contentplayuri,timeout,pps_headers,printflg=False):
    """
    ** CAN BE REMOVED - NO USE**
    To get the content start time from RM using the Scheduled ID

    :param protocol:
    :param rm_host:
    :param contentplayuri:
    :param timeout:
    :param pps_headers:
    :param printflg:
    :return:
    """
    try:
        #Get the Schedule ID from the conteplayuri of the recorded event
        contenturi = contentplayuri.split("=")
        contenturijoin = contenturi[1].split("&")
        scheduleId = contenturijoin[0]

        #Get the Content ID using RM CNS Response using the above Schedule ID
        url = protocol + "://" + rm_host + "/recordingInfo/" + scheduleId + "?contentType=MPEG4&mode=playback&responseFormat=json"
        print "URL to get the RM response :", url
        getrmresponse = sendURL("get",url,timeout,pps_headers)
        if getrmresponse is not None:
            if getrmresponse.status_code == 200:
                printLog("rm response:\n" + json.dumps(json.loads(getrmresponse.content),indent = 4, sort_keys = False),printflg)
                loadrmresponse = json.loads(getrmresponse.content)
                contentplaybackstarttime = loadrmresponse["playlist"]["segment"][0]["captureStartTime"]
                contentplaybackendtime = loadrmresponse["playlist"]["segment"][0]["captureEndTime"]
                if contentplaybackstarttime == "" and contentplaybackendtime == "":
                    print "ContentId is empty"
                    return None
                else:
                    return (contentplaybackstarttime,contentplaybackendtime)
            else:
                print "Not able to contentID because of RM Response failure"
                print getrmresponse.status_code
                print getrmresponse.headers
                print getrmresponse.content
                return None
        else:
            print "Not able to fetch RM Response"
            return None
    except:
        print "Problem in getting contentplayback starttime and endtime"
        PrintException()
        return None
####################################################################################################################
def get_contentURL_withoutPRM(protocol,playback_host,playback_port,playback_url,contentId,printflg=False):
    """
    construct the URL to download the m3u8 file to NPE component
    :param protocol:
    :param playback_host:
    :param playback_port:
    :param playback_url:
    :param contentId:
    :param printflg:
    :return:
    """
    try:
        contentURL = protocol + "://" + playback_host + ":" + str(playback_port) + playback_url + contentId + "/" + contentId + ".m3u8"
        return contentURL
    except:
        print "Problem in getting Content URL"
        PrintException()
        return None
####################################################################################################################
def teardownsmsession(protocol,sm_host,sm_port,smsessionId,printflg=False):

    try:
        #Teardown the Session
        smsessionidurl = protocol + "://" + sm_host + ":" + str(sm_port) + "/sm/streamingSession/" + smsessionId
        print "Delete the Session via " + smsessionidurl
        teardownsessionresponse = sendURL('delete',smsessionidurl)
        if teardownsessionresponse is not None:
            if teardownsessionresponse.status_code != 204:
                print "Problem in Tearing down the SM Session"
                print teardownsessionresponse.content
                print teardownsessionresponse.headers
                return None
            else:
                printLog("Session successfully deleted",printflg)
        else:
            print "Problem in getting the teardown session response"
            return None 
    except:
        print "Problem in tearing down the session"
        PrintException()
        return None
#######################################################################################################################
def get_numberoftuners(protocol,upm_host,upm_port,upm_headers,householdid,timeout):
    """
    Get the number of tuners from UPM for a household
    :param protocol:
    :param upm_host:
    :param upm_port:
    :param upm_headers:
    :param householdid:
    :param timeout:
    :return:
    """
    try:
        tuners_url = protocol + "://" + str(upm_host) + ":" + str(upm_port) + "/upm/households/" + householdid + "/numOfTuners"
        print "Getting Number of Tuners via " + tuners_url
        r = sendURL("get",tuners_url,timeout,upm_headers)
        if r.status_code != 200:
            print "problem accessing url" + tuners_url
            print r.headers
            print r.content
            return None
        else:
            numberoftuners = r.content
            print "Number of Tuners is " + numberoftuners
            return numberoftuners
    except:
        print "Error in finding number of tuners"
        PrintException()
        return None

########################################################################################################################
def set_numberoftuners(protocol,upm_host,upm_port,upm_headers,householdid,timeout,value):
    """
    Set the number of tuners for the household id
    :param protocol:
    :param upm_host:
    :param upm_port:
    :param upm_headers:
    :param householdid:
    :param timeout:
    :param value:
    :return:
    """
    try:
        tuners_url = protocol + "://" + str(upm_host) + ":" + str(upm_port) + "/upm/households/" + householdid + "/numOfTuners"
        print "Setting Number of Tuners via " + tuners_url
        r = sendURL("put",tuners_url,timeout,upm_headers,value)
        if r.status_code != 200:
            print "problem accessing url" + tuners_url
            print r.headers
            print r.content
            return "FAIL"
        else:
            return "PASS"
    except:
        print "Error in finding number of tuners"
        PrintException()

#########################################################################################################################
def get_contentIdlist_groupbyseries(contentId_dict,printflg=False):

    contentids = []
    contentstarttimelist = []
    contentdict = {}
    finalcontentidlist = []
    programidlist = []
    durationlist = []
    '''for key in contentId_dict.keys():
        subsplit = key.split('~')
        sub1 = subsplit[0]
        count = 0
        for sub in contentId_dict.keys():
            if sub1 in sub:
                count = count + 1
                continue
            else:
                continue
        if count > 1:
            pass
        else:
            del(contentId_dict[key])'''
    for key,value in contentId_dict.iteritems():
        if value:
            contentid = key
            contentstarttime = value[0]
            seriesId = value[3]
            duration = (value[1]-value[0])/1000
            contentids.append(contentid)
            contentstarttimelist.append(contentstarttime)
            durationlist.append(duration)
    mincontentstarttime = min(contentstarttimelist)
    #printLog("Least Content Start Time near to content time:\n" + str(mincontentstarttime),printflg)
    randomcontentidindex = contentstarttimelist.index(mincontentstarttime)
    random_contentId = contentids[randomcontentidindex]
    duration = durationlist[randomcontentidindex]
    #printLog("Content Id corresponding to that index:\n"+random_contentId,printflg)
    randomcontentIdsplit = random_contentId.split('~')
    programId = randomcontentIdsplit[0]
    for key,value in contentId_dict.iteritems():
        if programId in key:
            finalcontentidlist.append((key,value[0],value[3],duration))
    sortedcontentidlist = sorted(finalcontentidlist,key=lambda element:element[1])
    return sortedcontentidlist

############################################################################################################################################
def delete_seriesbookings(port,protocol,pps_host,pps_headers,timeout,contentURI,printflg=False):
    """
    Delete the series booking
    :param port:
    :param protocol:
    :param pps_host:
    :param pps_headers:
    :param timeout:
    :param contentURI:
    :param printflg:
    :return:
    """
    url =  protocol + "://" + pps_host + ":" + str(port) + contentURI + "/recurrence/bookings"
    print "Delete PPS booking via %s\n " %url
    r = sendURL ("delete",url,timeout,pps_headers)
    if r is not None :
        if r.status_code != 200:
            print "Pps Booking Failed via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return "FAIL"
        else:
            print "\nSeries Booking Deleted successfully"
            printLog("\nStatus Code : %s"%r.status_code,printflg)
            return "PASS"
    else:
        return "FAIL"
##############################################################################################################################################
def delete_seriesrecordings(port,protocol,pps_host,pps_headers,timeout,contentURI,printflg=False):
    """
    Delete the Series recording
    :param port:
    :param protocol:
    :param pps_host:
    :param pps_headers:
    :param timeout:
    :param contentURI:
    :param printflg:
    :return:
    """
    url =  protocol + "://" + pps_host + ":" + str(port) + contentURI + "/recurrence/episodes"
    print "Delete series booking via %s\n " %url
    r = sendURL ("delete",url,timeout,pps_headers)
    if r is not None :
        if r.status_code != 200:
            print "Deletion of series Booking Failed"
            print r.status_code
            print r.headers
            print r.content
            return "FAIL"
        else:
            print "\nSeries Booking and Recording Deleted successfully"
            printLog("\nStatus Code : %s"%r.status_code,printflg)
            return "PASS"
    else:
        return "FAIL"

##############################################################################################################################################
def booked_episodes(series_Id,event_state):
    """
    Get the details of the booked episode for a Series from the JSON response
    Details are [broadcasttime , endaailability, recordingID, uri, title, sheduleInstance, seriesId, shannelId]
    :param series_Id:
    :param event_state:
    :return:
    """
    event_state = json.loads(event_state.content)
    print "Series Id:",series_Id
    seriesdict ={}
    episodeNumberdisct={}
    if isinstance(event_state,list):
        for val in event_state:
            try:
                if val['content']['seriesId'] == series_Id:
                    episodeNumber =val['content']['episodeNumber']
                    print "Episode number :",episodeNumber
                    seriesdict.setdefault(episodeNumber,[])
                    contentStartTime = val['content']['broadcastDateTime']
                    contentEndTime = val['content']['endAvailability']
                    recordingId = val['recordingId']
                    booking_uri = val['uri']
                    booking_title = val['title']
                    contentId = val['scheduleInstance']
                    seriesId = val['seriesId']
                    serviceId = val['channelId']
                    duration = contentEndTime - contentStartTime
                    seriesdict[episodeNumber].append(contentStartTime)
                    seriesdict[episodeNumber].append(contentEndTime)
                    seriesdict[episodeNumber].append(duration)
                    seriesdict[episodeNumber].append(recordingId)
                    seriesdict[episodeNumber].append(booking_uri)
                    seriesdict[episodeNumber].append(booking_title)
                    seriesdict[episodeNumber].append(contentId)
                    seriesdict[episodeNumber].append(seriesId)
                    seriesdict[episodeNumber].append(serviceId)
                    (episodeNumberdisct.setdefault(episodeNumber,[])).extend(seriesdict.get(episodeNumber))
            except Exception as e:
                print "Exception :",str(e)
    if episodeNumberdisct :
        return(episodeNumberdisct)
    else:
        print "Error in retrieving booked episodes"
        return None
##############################################################################################################################################
def setStartGuardTime(protocol,pps_host,pps_port,contentURI,value,timeout):
    """

    Set the StartGuardTime for the booked event with the contentURL

    :param protocol:
    :param pps_host:
    :param pps_port:
    :param contentURI:
    :param value:
    :param timeout:
    :return:
    """
    try:
        headers = {
            'Content-Type': 'text/plain',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }
        url = protocol + "://" + pps_host + ":" + str(pps_port) + contentURI + "/startGuardTime"
        print "Post the StartGuardtime " + value + " to start the recording earlier via " + url
        setGuardTime = sendURL("put",url,timeout,headers,value)
        if setGuardTime is not None:
            if setGuardTime.status_code != 200:
                print "Setting GuardTime failed"
                print setGuardTime.status_code
                print setGuardTime.headers
                print setGuardTime.content
                return "FAIL"
            else:
                print "Setting Start Guard Time is successful"
                return "PASS"
        else:
            print "Error in setting Start Guard Time"
            return "FAIL"
    except:
        print "Error occurred in setting Start Guard Time"
        return "FAIL"
##############################################################################################################################################
def setEndGuardTime(protocol,pps_host,pps_port,contentURI,value,timeout):
    """
    Set the EndGuardTime for the booked content with the contentURL
    :param protocol:
    :param pps_host:
    :param pps_port:
    :param contentURI:
    :param value:
    :param timeout:
    :return:
    """
    try:
        headers = {
            'Content-Type': 'text/plain',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }
        url = protocol + "://" + pps_host + ":" + str(pps_port) + contentURI + "/endGuardTime"
        print "Post the EndGuardtime " + value + " to start the recording earlier via " + url
        setGuardTime = sendURL("put",url,timeout,headers,value)
        if setGuardTime is not None:
            if setGuardTime.status_code != 200:
                print "Setting GuardTime failed"
                print setGuardTime.status_code
                print setGuardTime.headers
                print setGuardTime.content
                return "FAIL"
            else:
                print "Setting End Guard Time is successful"
                return "PASS"
        else:
            print "Error in setting End Guard Time"
            return "FAIL"
    except:
        print "Error occurred in setting End Guard Time"
        return "FAIL"
#######################################################################################################################
def verifyplaybackstarttime(recordingstarttime,recordingduration,playbackstarttime,playbackendtime):
    """
    Verify the start time and duration of a recording

    Used in the Playback funciton to verify the starttime

    :param recordingstarttime:
    :param recordingduration:
    :param playbackstarttime:
    :param playbackendtime:
    :return:
    """
    try:
        recordingstarttimeinepoch = iso2epoch(recordingstarttime)
        print "recording start time : " + str(recordingstarttimeinepoch)
        recordingdurationinseconds = isotimetoseconds(recordingduration)
        print "recording duration : " + str(recordingdurationinseconds)
        recordingendtimeinepoch = recordingstarttimeinepoch + recordingdurationinseconds
        print "recording endtime in epoch : " + str(recordingendtimeinepoch)
        recordingendtime = epoch2iso(recordingendtimeinepoch)
        print "recording end time : " + recordingendtime
        if abs(recordingstarttimeinepoch - iso2epoch(playbackstarttime)) <= 2 and abs(recordingendtimeinepoch - iso2epoch(playbackendtime)) <= 2:
            return "PASS"
        else:
            print "Recording start time : ", recordingstarttime
            print "Playback start time : ", playbackstarttime
            print "Playback end time : ", playbackendtime
            return "FAIL"
    except:
        print "Error occurred in verifying playback"
        PrintException()
        return "FAIL" 
######################################################################################################################3
def stoprecording(protocol,pps_host,pps_port,contenturi,timeout):
    """
    Stop the ongoing recording.
    The recording will be stopped and moved to the Recorded state
    :param protocol:
    :param pps_host:
    :param pps_port:
    :param contenturi:
    :param timeout:
    :return:
    """
    try:
        headers = {
            'Content-Type': 'text/plain',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Accept': 'application/json'
            }
        url = protocol + "://" + pps_host + ":" + str(pps_port) + contenturi + "/management"
        print "Stop the recording via " + url
        stop_recording = sendURL("post",url,timeout,headers,"stop")
        if stop_recording is not None:
            if stop_recording.status_code != 200:
                print "Stop Recording Failed"
                print stop_recording.status_code
                print stop_recording.headers
                print stop_recording.content
                return "FAIL"
            else:
                print "Stop Recording is successful"
                return "PASS"
        else:
            print "Error in Stopping the Recording"
            return "FAIL"
    except:
        print "Error occurred while Stopping the Recording"
        return "FAIL"
##################################################################################################################################
def cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout):
    """

    Delete the PPS Booking and PPS Recording

    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param pps_headers:
    :param timeout:
    :return:
    """
    try:
        event_state = fetch_bookingCatalog(pps_port,protocol,pps_host,householdid,timeout)
        time.sleep(5)
        if event_state :
            event_state = json.loads(event_state.content)
            for val in event_state:
                if val['uri']:
                    print val['uri']
                    uri_delete = val['uri']
                    delete_PPSbooking(pps_port,protocol,pps_host,pps_headers,timeout,uri_delete,printflg=False)
                else:
                    pass
        event_state1 = fetch_recordingCatalog(pps_port,protocol,pps_host,householdid,timeout)
        time.sleep(5)
        if event_state1 :
            event_state2 = json.loads(event_state1.content)
            for val in event_state2:
                if val['uri']:
                    print val['uri']
                    uri_delete = val['uri']
                    delete_PPSrecording(pps_port,protocol,pps_host,pps_headers,timeout,uri_delete,printflg=False)
                else:
                    pass        
    except:
        pass
#############################################################################################################################################
def cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout):
    """

    Reset the Household to the original state.
    Remove all the bookings, recordings, recoreded and failed contents, reset the tuner quota and disk quota

    :param cfg:
    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param pps_headers:
    :param timeout:
    :return:
    """
    try:
        print "\n" + "#"*20 + " HOUSEHOLD CLEANUP STARTED "+ "#"*20+ "\n"
        default_disk_quota = cfg['quotas']['diskQuota']
        default_tuner_quota = cfg['quotas']['numOfTuners']
        upm_host = cfg['upm']['host']
        upm_port = cfg['upm']['port']
        upm_headers = {
                  'Content-Type':'text/plain',
                  'Source-Type':'WEB',
                  'Source-ID':'127.0.0.1',
                   'Accept': 'text/plain',
                 }
        upm_headers1 = {
                   'Content-Type':'text/plain',
                   'Source-Type':'WEB',
                   'Source-ID':'211.209.128.25',
                }
        blockPrint() #Disabling the Prints in all called functions
        #fetch household catalog and delete the series recurrences
        event_state = fetch_household_Catalog(pps_port,protocol,pps_host,householdid,timeout)
        time.sleep(5)
        if event_state :
            skipcheck=[]
            event_state = json.loads(event_state.content)
            for val in event_state:
                if val['uri'] and val['recurrence']=="SERIES" and val['seriesId'] not in skipcheck:
                    print val['uri']
                    uri_delete = val['uri']
                    skipcheck.append(val['seriesId'])
                    stop_delete_series_recurrence(pps_port,protocol,pps_host,uri_delete,timeout,printflg=False)
                else:
                    pass

        #Fetch the booking catalog and delete the full catalog items
        event_state = fetch_bookingCatalog(pps_port,protocol,pps_host,householdid,timeout)
        time.sleep(5)
        if event_state :
            event_state = json.loads(event_state.content)
            for val in event_state:
                if val['uri']:
                    print val['uri']
                    uri_delete = val['uri']
                    delete_PPSbooking(pps_port,protocol,pps_host,pps_headers,timeout,uri_delete,printflg=False)
                else:
                    pass
        event_state1 = fetch_recordingCatalog(pps_port,protocol,pps_host,householdid,timeout)
        time.sleep(5)
        #Fetch the recording catalog and delete the full catalog items
        if event_state1 :
            event_state2 = json.loads(event_state1.content)
            for val in event_state2:
                if val['uri']:
                    print val['uri']
                    uri_delete = val['uri']
                    delete_PPSrecording(pps_port,protocol,pps_host,pps_headers,timeout,uri_delete,printflg=False)
                else:
                    pass
        event_state3 = fetch_failedrecording_catalog(pps_port,protocol,pps_host,householdid,timeout)
        time.sleep(5)
        #Fetch the failed recording catalog and delete the full catalog items
        if event_state3 :
            event_state4 = json.loads(event_state3.content)
            for val in event_state4:
                if val['uri']:
                    print val['uri']
                    uri_delete = val['uri']
                    delete_PPSrecording(pps_port,protocol,pps_host,pps_headers,timeout,uri_delete,printflg=False)
                else:
                    pass
        #Set the default values for Diskquota and Tunerquota received from the Config File
        household_disk_quota = fetch_full_details_diskquota(protocol,upm_host,upm_port,householdid,timeout,printflg=False)
        household_tuner_quota = get_numberoftuners(protocol,upm_host,upm_port,upm_headers,householdid,timeout)
        if (str(default_disk_quota) == household_disk_quota.content) and (household_tuner_quota == str(default_tuner_quota)):
            pass
        else:
            set_numberoftuners(protocol,upm_host,upm_port,upm_headers1,householdid,timeout,str(default_tuner_quota))
            modify_diskQuota(cfg,protocol,upm_host,upm_port,householdid,str(default_disk_quota),upm_headers1,timeout,printflg=False)
        enablePrint() #Re-enabling the prints to print the below line and all successive prints
        # print "Household %s catalogs cleaned up successfully" %householdid
    except:
        enablePrint() #Re-enabling the prints to print the exception and all successive prints
        PrintException()
    finally:
        enablePrint() #Reenabling the prints to print the final line and all successive prints
        print "\n" + "#"*20 + " HOUSEHOLD CLEANUP ENDED   "+ "#"*20+ "\n"
#############################################################################################################################################
def delete_events_from_booklist(port,protocol,pps_host,householdid,contentId_value,pps_headers,timeout):
    """
    Delete the content based on the content id
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param contentId_value:
    :param pps_headers:
    :param timeout:
    :return:
    """
    event_state = fetch_catalogbyContentId(port,protocol,pps_host,householdid,contentId_value,timeout)
    time.sleep(5)
    event_state = json.loads(event_state.content)
    if isinstance(event_state,list):
        for val in event_state:
          uri_delete = val['uri']
          deleted =delete_PPSbooking(port,protocol,pps_host,pps_headers,timeout,uri_delete,printflg=False)
    if deleted == "PASS":
       return("PASS")
    else:
       return("FAIL")
###########################################################################################################################################
def get_series_contentIddict_bytitle(json_responce,title=None,serviceparameterlist=[]):
    """
    Get the Content IDs and the details of the Series only for future event.
    Details includes broadcasttime and endavailabiltiy

    :param json_responce:
    :param title:
    :param serviceparameterlist:
    :return:
    """
    contents=json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict={}
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if value['seriesId'] :
                        if title in value['title']:
                            if value['broadcastDateTime'] > long(current_time) and value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                                contentId = value['id'] + "~" + value['instanceId']
                                contentId_Dict.setdefault(contentId,[])
                                #if value['broadcastDateTime'] > long(current_time) and value['endAvailability']>long(current_time):
                                contentStartTime = value['broadcastDateTime']
                                contentEndTime = value['endAvailability']
                                contentId_Dict[contentId].append(contentStartTime)
                                contentId_Dict[contentId].append(contentEndTime)
                                if serviceparameterlist:
                                    for serviceparameter in serviceparameterlist:
                                        listparameter = value[serviceparameter]
                                        contentId_Dict[contentId].append(listparameter)
                except:
                   pass
    if not bool(contentId_Dict):    
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "Content ID Dictionary is empty"        
        return None
    else:
        return(contentId_Dict)
###########################################################################################################################################
def get_series_contentIddict_currentandfuture_bytitle(json_responce, title=None, serviceparameterlist=[]):
    """
    Get the Content IDs and the details of the Series for current and future episode.
    Atleat one episode should be ongoing.
    Details includes broadcasttime and endavailabiltiy

    :param json_responce:
    :param title:
    :param serviceparameterlist:
    :return:
    """
    contents=json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict={}
    current_id = 0
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if value['seriesId'] :
                        if title in value['title']:
                            endtime_difference = get_timedifference(value['endAvailability'],printflg=False) 
                            contentId = value['id'] + "~" + value['instanceId']
                            contentId_Dict.setdefault(contentId,[])
                            if value['broadcastDateTime'] < long(current_time) and endtime_difference > 120 and value['cdvrAvailable'] == True:
                                current_id = current_id + 1 
                                contentStartTime = value['broadcastDateTime']
                                contentEndTime = value['endAvailability']
                                duration = contentEndTime - contentStartTime
                                contentId_Dict[contentId].append(contentStartTime)
                                contentId_Dict[contentId].append(contentEndTime)
                                contentId_Dict[contentId].append(duration)
                                if serviceparameterlist:
                                    for serviceparameter in serviceparameterlist:
                                        listparameter = value[serviceparameter]
                                        contentId_Dict[contentId].append(listparameter)
                            elif value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                                contentStartTime = value['broadcastDateTime']
                                contentEndTime = value['endAvailability']
                                duration = contentEndTime - contentStartTime
                                contentId_Dict[contentId].append(contentStartTime)
                                contentId_Dict[contentId].append(contentEndTime)
                                contentId_Dict[contentId].append(duration)
                                if serviceparameterlist:
                                    for serviceparameter in serviceparameterlist:
                                        listparameter = value[serviceparameter]
                                        contentId_Dict[contentId].append(listparameter)
                except:
                   pass
    if not bool(contentId_Dict):
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "Content ID Dictionary is empty"
        return None
    else:
        if current_id:
            return(contentId_Dict)
        else:
            return None
#######################################################################################################################################################
def Verify_Series_Collapse(group_id_list,port,protocol,pps_host,householdid,timeout,printflg=False):
    count  = 0
    if isinstance(group_id_list,list):
        if group_id_list :
            print "group id list" , group_id_list
            for group_id in group_id_list :
                url =  protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog?collapse=true"
                print "series collapse via url %s\n " %url
                r = sendURL ("get",url,timeout)
                if r is not None :
                    if r.status_code != 200:
                        print "series collaspe fetching failed via  url %s"%url
                        print r.status_code
                        print r.headers
                        print r.content
                        return ("FAIL",None)
                    else:
                        if r.content == "[]":
                            print "series collaspe Response is empty"
                            return ("FAIL",None)
                        else:
                             temp = Inner_Series_collaspe_verification(r.content,group_id)
                             if temp  == "PASS" :
                                count = count + 1
                else:
                    print "unable to fetch series collaspe response"
                    return ("FAIL",None)
            if count  == len(group_id_list):
                   print "series collapsed successfully"
                   return ("PASS",r)
            else:
                print "series does not collapse successfully"
                return ("FAIL",None)
        else:
             print "unable to fetch series collaspe response"
             return ("FAIL",None)
    else:
        print "unable to fetch series collaspe response"
        return ("FAIL",None)

#######################################################################################################################################################
def Verify_Series_expand(group_id_list,port,protocol,pps_host,householdid,timeout,printflg=False):
    count  = 0
    if isinstance(group_id_list,list):
      if group_id_list :
        print "group id list" , group_id_list
        for group_id in group_id_list :
            url =  protocol + "://" + str(pps_host) + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog?filter:series=" + str(group_id) + "&collapse=true"
            print "series expand via %s\n " %url
            r = sendURL ("get",url,timeout)
            if r is not None :
                if r.status_code != 200:
                    print "series expand failed  via  url %s"%url
                    print r.status_code
                    print r.headers
                    print r.content
                    return ("FAIL",None)
                else:
                    if r.content == "[]":
                        print " Service Response is empty"
                        return ("FAIL",None)
                    else:
                         temp = Inner_Series_expand_verification(r.content,group_id)
                         if temp  == "PASS" :
                            count = count + 1
            else:
                print "Not able to fetch Grid Response"
                return ("FAIL",None)
        if count  == len(group_id_list):
                print "series expanded successfully"
                return ("PASS",r)
        else:
              print "series does not expand successfully"
              return ("FAIL",None)
      else:
         print "group id list is empty "
         return ("FAIL",None)
    else:
         print "group id list is empty "
         return ("FAIL",None)
#################################################################################################################################################
def Inner_Series_expand_verification(response,group_id):
    count = 0
    main = json.loads(response)
    for val in main :
        if group_id in val['seriesId']:
           count = count + 1
    if count :
        print "series expansion is successful"
        return "PASS"
    else:
        print "series expansion is  not successful"
        return "FAIL"
#################################################################################################################################################
def Inner_Series_collaspe_verification(response,group_id):
    count = 0
    main = json.loads(response)
    for val in main :
        if group_id  == val['contentId'] and  val['type'] == "COLLAPSED-INSTANCE":
           count = count + 1
    if count :
        print "series collapse is successful"
        return "PASS"
    else:
        print "series collapse is  not successful"
        return "FAIL"

#################################################################################################################################################
def createbookmark_recordedcontent(protocol,pps_host,pps_port,pps_headers,householdid,contentId,pausepositionvalue,pausepositiontagname,timeout):
    try:
        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/households/" + householdid + "/bookmarks/" + contentId
        print "Create the bookmark and pause the playback via " + url
        bookmark_payload = """{
            "position":"%s",
            "tag":"%s"
            }""" %(pausepositionvalue,pausepositiontagname)
        createbookmark = sendURL("post",url,timeout,pps_headers,bookmark_payload)
        if createbookmark is not None:
            if createbookmark.status_code != 201:
                print "Creating Bookmark failed"
                print createbookmark.status_code
                print createbookmark.headers
                print createbookmark.content
                return "FAIL"
            else:
                print "Creating Bookmark and pausing the playback is successful"
                return "PASS"
        else:
            print "Error in creating the Bookmark for the recorded content"
            return "FAIL"
    except:
        print "Error occurred in creating the bookmark"
        return "FAIL"
##################################################################################################################################################
def updatebookmark_recordedcontent(protocol,pps_host,pps_port,householdid,contentId,updatepausepositionvalue,pausepositiontagname,timeout):
    try:
        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/households/" + householdid + "/bookmarks/" + contentId + "/" + pausepositiontagname
        print "Update the bookmark and pause the playback via " + url
        pps_headers = {
            'Content-Type': 'text/plain'
        }
        updatebookmark = sendURL("put",url,timeout,pps_headers,updatepausepositionvalue)
        if updatebookmark is not None:
            if updatebookmark.status_code != 200:
                print "Updating Bookmark failed"
                print updatebookmark.status_code
                print updatebookmark.headers
                print updatebookmark.content
                return "FAIL"
            else:
                print "Updating Bookmark and pausing the playback is successful"
                return "PASS"
        else:
            print "Error in Updating the Bookmark for the recorded content"
            return "FAIL"
    except:
        print "Error occurred in Updating the bookmark"
        return "FAIL"
####################################################################################################################################################
def retrievebookmark_recordedcontent(protocol,pps_host,pps_port,householdid,contentId,pausepositiontagname,timeout):
    try:
        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/households/" + householdid + "/bookmarks/" + contentId + "/" + pausepositiontagname
        print "Retreive the bookmark and resume the playback via " + url
        pps_headers = {
            'Accept': 'text/plain'
        }
        retrievebookmark = sendURL("get",url,timeout,pps_headers)
        if retrievebookmark is not None:
            if retrievebookmark.status_code != 200:
                print "Retrieving Bookmark failed"
                print retrievebookmark.status_code
                print retrievebookmark.headers
                print retrievebookmark.content
                return None
            else:
                print "Retrieving Bookmark is successful"
                return retrievebookmark
        else:
            print "Error in Retrieving the Bookmark for the Paused Playback"
            return None
    except:
        print "Error occurred in Retrieving the bookmark"
        return None
#######################################################################################################################################################
def deletebookmark_recordedcontent(protocol,pps_host,pps_port,householdid,contentId,pausepositiontagname,timeout):
    try:
        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/households/" + householdid + "/bookmarks/" + contentId + "/" + pausepositiontagname
        print "Delete the bookmark via " + url
        deletebookmark = sendURL("delete",url,timeout)
        if deletebookmark is not None:
            if deletebookmark.status_code != 200:
                print "Deleting Bookmark failed"
                print deletebookmark.status_code
                print deletebookmark.headers
                print deletebookmark.content
                return "FAIL"
            else:
                print "Deleting Bookmark is successful"
                return "PASS"
        else:
            print "Error in Deleting the Bookmark"
            return "FAIL"
    except:
        print "Error occurred in Deleting the bookmark"
        return "FAIL"
#############################################################################################################################################
def get_contentIddict_bytitle(json_responce,title,serviceparameterlist=[]):
    """
    Get the Content IDs and the details of the Series only for future event.
    Details includes broadcasttime, endavailabiltiy and duration

    :param json_responce:
    :param title:
    :param serviceparameterlist:
    :return:
    """
    contents=json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict={}
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if title in value['title']:
                        if value['broadcastDateTime'] > long(current_time) and value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                            contentId = value['id'] + "~" + value['instanceId']
                            contentId_Dict.setdefault(contentId,[])
                            #if value['broadcastDateTime'] > long(current_time) and value['endAvailability']>long(current_time):
                            contentStartTime = value['broadcastDateTime']
                            contentEndTime = value['endAvailability']
                            duration = contentEndTime - contentStartTime
                            contentId_Dict[contentId].append(contentStartTime)
                            contentId_Dict[contentId].append(contentEndTime)
                            contentId_Dict[contentId].append(duration)
                            if serviceparameterlist:
                                for serviceparameter in serviceparameterlist:
                                    listparameter = value[serviceparameter]
                                    contentId_Dict[contentId].append(listparameter)
                        else:
                            print "Current Time:", datetime.datetime.utcnow()
                            print "Content StartTime:", value['broadcastDateTime']
                            print "Content EndTime:", value['endAvailability']
                except:
                   print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                   print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
                   print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                   print "Exception Occurred while getting content Dict"
                   PrintException()
                   return None
    if not bool(contentId_Dict):     
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "Content ID Dictionary is empty"        
        return None
    else:
        return(contentId_Dict)
###################################################################################################################################################
def delete_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,servicelist,upm_headers,timeout):
    """
    Delete the Enabled services of the Household like CDVR, RESTART, CATCHUP etc..
    :param protocol:
    :param upm_host:
    :param upm_port:
    :param householdid:
    :param servicelist:
    :param upm_headers:
    :param timeout:
    :return:
    """
    try:
        deleteservicepasscount = 0
        if isinstance(servicelist,list):
            for enabledservicename in servicelist:
                url = protocol + "://" + upm_host + ":" + str(upm_port) + "/upm/households/" + householdid + "/enabledServices/" + enabledservicename
                print "Delete the specific service for household via " + url
                deleteservice = sendURL("delete",url,timeout,upm_headers)
                if deleteservice is not None:
                    if deleteservice.status_code != 200:
                        print "Deleting Service for the household failed"
                        print deleteservice.status_code
                        print deleteservice.headers
                        print deleteservice.content
                        return "FAIL"
                    else:
                        deleteservicepasscount += 1
                else:
                    print "Error in Deleting the Service"
                    return "FAIL"
        else:
            print "Provided Servicelist is not of list type"
            return "FAIL"
        if deleteservicepasscount >= 1:
            print "Deleting Enabled Services is successful"
            return "PASS"
        else:
            print "Deleting Service Failed"
            return "FAIL"
    except:
        print "Error occurred in Deleting the Service"
        return "FAIL"
##################################################################################################################################################
def set_HouseholdEnabledService(protocol,upm_host,upm_port,householdid,servicelist,upm_headers,timeout):
    """

    Set the Household enabled services

    :param protocol:
    :param upm_host:
    :param upm_port:
    :param householdid:
    :param servicelist:
    :param upm_headers:
    :param timeout:
    :return:
    """
    try:
        enabledservicepasscount = 0
        if isinstance(servicelist,list):
            for enabledservicename in servicelist:
                url = protocol + "://" + upm_host + ":" + str(upm_port) + "/upm/households/" + householdid + "/enabledServices/" + enabledservicename
                print "Enable the specific service for household via " + url
                enableservice = sendURL("put",url,timeout,upm_headers,'')
                if enableservice is not None:
                    if enableservice.status_code != 200:
                        print "Enabling Service for the household failed"
                        print enableservice.status_code
                        print enableservice.headers
                        print enableservice.content
                        return "FAIL"
                    else:
                        enabledservicepasscount += 1
                else:
                    print "Error in Enabling the Service"
                    return "FAIL"
        else:
            print "Provided Servicelist is not of list type"
            return "FAIL"
        if enabledservicepasscount >= 1:
            print "Enabling Services is successful"
            return "PASS"
        else:
            print "Enabling Services failed"
            return "FAIL" 
    except:
        print "Error occurred in Deleting the Service"
        return "FAIL"
##################################################################################################################################################
def get_HouseholdEnabledServices(protocol,upm_host,upm_port,householdid,upm_headers,timeout):
    """
    Get the Household enabled services
    :param protocol:
    :param upm_host:
    :param upm_port:
    :param householdid:
    :param upm_headers:
    :param timeout:
    :return:
    """
    try:
        url = protocol + "://" + upm_host + ":" + str(upm_port) + "/upm/households/" + householdid + "/enabledServices"
        print "Fetch the list of services for household via " + url
        getservicelist = sendURL("get",url,timeout,upm_headers)
        if getservicelist is not None:
            if getservicelist.status_code != 200:
                print "Getting Services for the household failed"
                print getservicelist.status_code
                print getservicelist.headers
                print getservicelist.content
                return None
            else:
                if getservicelist.content != "[]":
                    print "Getting Household Servicelist is successful"
                    return getservicelist.content
                else:
                    print "Service List is Empty"
                    return None
        else:
            print "Error in Getting the Household Servicelist"
            return None
    except:
        print "Error occurred in Getting the Servicelist"
        return None

#####################################################################################################################
def get_currentandfuture_contentIddict(json_responce,title,serviceparameterlist=[]):
    """
    Get the Content IDs and the details of the Events for current and future event.
    Atleat one episode should be ongoing.
    Details includes broadcasttime , endavailabiltiy and duration

    :param json_responce:
    :param title:
    :param serviceparameterlist:
    :return:
    """
    contents=json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict={}
    current_id = 0
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if title in value['title']:
                        contentId = value['id'] + "~" + value['instanceId']
                        contentId_Dict.setdefault(contentId,[])
                        endtime_difference = get_timedifference(value['endAvailability'],printflg=False)  
                        if value['broadcastDateTime'] < long(current_time) and endtime_difference >= 120 and value['cdvrAvailable'] == True:
                            current_id = current_id + 1                            
                            contentStartTime = value['broadcastDateTime']
                            contentEndTime = value['endAvailability']
                            duration = contentEndTime - contentStartTime
                            contentId_Dict[contentId].append(contentStartTime)
                            contentId_Dict[contentId].append(contentEndTime)
                            contentId_Dict[contentId].append(duration)
                            if serviceparameterlist:
                                for serviceparameter in serviceparameterlist:
                                    listparameter = value[serviceparameter]
                                    contentId_Dict[contentId].append(listparameter)                             
                        elif value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                            contentStartTime = value['broadcastDateTime']
                            contentEndTime = value['endAvailability']
                            duration = contentEndTime - contentStartTime
                            contentId_Dict[contentId].append(contentStartTime)
                            contentId_Dict[contentId].append(contentEndTime)
                            contentId_Dict[contentId].append(duration)
                            if serviceparameterlist:
                                for serviceparameter in serviceparameterlist:
                                    listparameter = value[serviceparameter]
                                    contentId_Dict[contentId].append(listparameter)
                        else:
                            print "Current Time:", datetime.datetime.utcnow()
                            print "Content StartTime:", value['broadcastDateTime']
                            print "Content EndTime:", value['endAvailability']
                except:
                   print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                   print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
                   print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                   print "Exception Occurred while getting content Dict"
                   PrintException()
                   return None
    if not bool(contentId_Dict):
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "Content ID Dictionary is empty"
        return None
    else:
        if current_id:  
            return(contentId_Dict)
        else:
            return None 
#######################################################################################################################

def do_PPSbooking_returnresponse(port,protocol,pps_host,householdid,pps_headers,payload,random_contentId,timeout,printflg=False):

    """
    Do a PPS booking and return STATUS along with PPS response
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param pps_headers:
    :param payload:
    :param random_contentId:
    :param timeout:
    :param printflg:
    :return:
    """

    url =  protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/bookings"
    print "\nPPS Booking via : ",url
    r = sendURL ("post",url,timeout,pps_headers,payload)
    if r is not None :
        if r.status_code != 201:
            print "PPS Booking Failed via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return ("FAIL",r)
        else:
            printLog("\nPPS Booking successfully for : %s"%random_contentId,printflg)
            printLog("\nStatus Code : %s"%r.status_code,printflg)
            return ("PASS",r)
    else:
        return ("FAIL",None)
#######################################################################################################################

def modify_autoDeleteDays(protocol,pps_host,port_pps,householdid,autoDeleteDays,autoDeleteDays_headers,timeout,uri,printflg=False):
    """

    Modify the auto delete days of an event

    :param protocol:
    :param pps_host:
    :param port_pps:
    :param householdid:
    :param autoDeleteDays:
    :param autoDeleteDays_headers:
    :param timeout:
    :param uri:
    :param printflg:
    :return:
    """
    try :
        url = protocol + "://"+ pps_host + ":" + str(port_pps) + "/pps/households/" + str(householdid) + "/catalog/" + str(uri)+ "/autoDeleteDays"
        r = sendURL ("put",url,timeout,autoDeleteDays_headers,str(autoDeleteDays))
        print "Autodeletedays is modified  via URL : ", url
        if r is not None :
            if r.status_code != 200:
                print "Autodeletedays modification failed  via URL %s"%url
                print r.status_code
                print r.headers
                print r.content
                return("FAIL")
            else:
                return("PASS")
        return("FAIL")
    except:
        return("FAIL")
#######################################################################################################################

def modify_autodeletedays_series(protocol,pps_host,port_pps,householdid,autoDeleteDays,autoDeleteDays_headers,timeout,uri,printflg=False):
    """
    Modify the auto delete days of the Series
    :param protocol:
    :param pps_host:
    :param port_pps:
    :param householdid:
    :param autoDeleteDays:
    :param autoDeleteDays_headers:
    :param timeout:
    :param uri:
    :param printflg:
    :return:
    """

    try :
        url = protocol + "://"+ pps_host + ":" + str(port_pps) + "/pps/households/" + str(householdid) + "/catalog/" + str(uri)+ "/recurrence/autoDeleteDays"
        r = sendURL ("put",url,timeout,autoDeleteDays_headers,str(autoDeleteDays))
        print "Autodeletedays is modified  via URL : ", url
        if r is not None :
            if r.status_code != 200:
                print "Autodeletedays modification failed  via URL %s"%url
                print r.status_code
                print r.headers
                print r.content
                return("FAIL")
            else:
                return("PASS")
        return("FAIL")
    except:
        return("FAIL")



#######################################################################################################################

def fetch_autoDeleteDays(bookedcatalogresponse,random_contentId):
    """
    Get the auto delete days  from the JSON response

    :param bookedcatalogresponse:
    :param random_contentId:
    :return:
    """
    autoDeleteDays = None
    try:
       event_state = json.loads(bookedcatalogresponse.content)
       for val in event_state:
           try:
               if val["scheduleInstance"] == random_contentId :
                  autoDeleteDays = val['autoDeleteDays']
           except:
               pass
       return autoDeleteDays
    except:
        print "Not able to retrieve autoDeleteDays from the booked catalog"
        return autoDeleteDays

#######################################################################################################################

def verify_recording_state(pps_port,protocol,pps_host,householdid,content_id,timeout):
    """

    Verify the contentid is in recording state.

    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param content_id:
    :param timeout:
    :return:
    """
    try:
        content_id_list = []
        if isinstance(content_id, list):
            content_id_list = content_id
        else:
            content_id_list = [content_id]

        jsonrecordingcatalog = None
        #recording_state = 0
        recording_content = []
        jsonrecordingcatalog = fetch_recordingCatalog(pps_port,protocol,pps_host,householdid,timeout)
        if jsonrecordingcatalog:
            jsonrecordingcontent = json.loads(jsonrecordingcatalog.content)
            for val,items in enumerate(jsonrecordingcontent):
                try:
                    if items['scheduleInstance'] in content_id_list:
                        if items['state'] == "RECORDING":
                            recording_content.append(items['scheduleInstance'])
                            #recording_state = recording_state + 1
                except:
                     pass
        else:
            message = "Recording catalog is empty"
            print message
            return ("FAIL",message)

        if len(recording_content) == len(content_id_list):
            print "All Program with the contentid %s is in RECORDING state" %content_id_list
            return ("PASS",jsonrecordingcatalog)
        else:
            message = "Programs not in recording state : %s " % (str(list(set(content_id_list) - set(recording_content))))
            print message
            return ("FAIL",message)
    except:
        message = "Error occured:" + PrintException(True)
        print message
        return ("EXCEPTION_FAILURE",message)
#######################################################################################################################

def verify_recorded_state(pps_port,protocol,pps_host,householdid,contentid_list,timeout, verify_vmr=True):
    """
    Verify the contentid is in Recorded state
    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param contentid_list:
    :param timeout:
    :return:
    """
    try:
        content_id_list = []
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        members = inspect.getmembers(mod)
        if isinstance(contentid_list, list):
          content_id_list = contentid_list
        else :
          content_id_list = [contentid_list]
        jsonrecordingcatalog = None
        recorded_state = 0
        recorded_content = []
        jsonrecordingcatalog = fetch_recordingCatalog(pps_port,protocol,pps_host,householdid,timeout)
        if jsonrecordingcatalog:
            jsonrecordingcontent = json.loads(jsonrecordingcatalog.content)
            for items in jsonrecordingcontent:
                try:
                    if items['scheduleInstance'] in content_id_list:
                        bookedDuration = items['bookingDuration']
                        val = time.strptime(bookedDuration, "%H:%M:%S")
                        bookedDuration = datetime.timedelta(hours=val.tm_hour, minutes=val.tm_min, seconds=val.tm_sec)\
                            .seconds
                        actualDuration = items['duration']
                        val1 = time.strptime(actualDuration, "%H:%M:%S")
                        actualDuration = datetime.timedelta(hours=val1.tm_hour, minutes=val1.tm_min, seconds=val1.tm_sec)\
                            .seconds

                        if items['state'] == "RECORDED":
                            if "stoprecording" in chain.from_iterable(members):
                                recorded_state = recorded_state + 1
                                recorded_content.append(items['scheduleInstance'])
                            else:
                                if (bookedDuration - actualDuration) >= 0:
                                    recorded_state = recorded_state + 1
                                    recorded_content.append(items['scheduleInstance'])
                                else:
                                    print "Content bookingDuration is less than duration : %s" %str(items['scheduleInstance'])

                except:
                     pass
        else:
            message = "Recorded catalog is empty"
            print message
            return "FAIL",message

        if recorded_state == len(content_id_list):
            print "All Programs with the contentids %s is in RECORDED state" %content_id_list
            return "PASS", jsonrecordingcatalog
        else:
            #message = "All programs with the contentids %s is not in RECORDED state" %content_id_list
            message = "Programs not in recorded state : %s " % (str(list(set(content_id_list) - set(recorded_content))))
            print message
            if verify_vmr:
                # Verifying the VMR response
                frm = inspect.stack()[-2]
                conf = frm[0].f_globals['cfg']
                result, vmr_response = verify_vmr_response_status(conf, pps_host, pps_port, protocol, [householdid],
                                                                  content_id_list, timeout)
                if result and vmr_response:
                    print "VMR Response : " + json.dumps(json.loads(vmr_response.content), indent=4, sort_keys=False)
                else:
                    message = "Unable to fetch VMR response. VMR response is None"
                    return "FAIL", message
            return "FAIL", message
    except:
        message = "Error occured:" + PrintException(True)
        print message
        return ("EXCEPTION_FAILURE",message)

#######################################################################################################################

def verify_booking(pps_port,protocol,pps_host,householdid,random_contentId_list,timeout):
    """

    Verify the content id list is either in booked or recording state

    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param random_contentId_list:
    :param timeout:
    :return:
    """
    try:
       contentId_list = []
       if isinstance(random_contentId_list,list):
          contentId_list = random_contentId_list
       else :
          contentId_list = [random_contentId_list]

       r = None
       count_contentId = 0
       r = fetch_bookingCatalog(pps_port,protocol,pps_host,householdid,timeout)
       if r is not None :
           event_state = json.loads(r.content)
           for temp in contentId_list:
               for val in event_state:
                   try:
                       if val["scheduleInstance"] == temp:
                          if (val['state'] == "BOOKED" or val['state']== "RECORDING"):
                              count_contentId = count_contentId + 1
                   except:
                      pass
       else:
           print "Booked catalog is empty"
           return ("FAIL",None)
       if count_contentId == len(contentId_list):
           print "All programs with the contentids %s is in BOOKED state" %contentId_list
           return ("PASS",r)
       else:
           print "All programs with the contentids %s is not in BOOKED state" %contentId_list
           return ("FAIL",None)
    except:
       print "Error  occurred " + PrintException(True)
       return ("EXCEPTION_FAILURE",None)

###########################################################################################################################

def fetch_autoDeleteDays_TimeBased(catalog_responce,programstarttimeiniso):
    """
    Fetch auto delete days if the booking is TIME based from the JSON resonse

    :param catalog_responce:
    :param programstarttimeiniso:
    :return:
    """
    autoDeleteDays = None
    try:
       catalog_content = json.loads(catalog_responce.content)
       for val in catalog_content:
          try:
              if val['bookingType'] == "TIME" :
                  if val['bookingStartTime'] == programstarttimeiniso:
                      autoDeleteDays = val['autoDeleteDays']
          except:
              pass
       return autoDeleteDays
    except:
       print "Not able to retrieve autoDeleteDays from the booked catalog"
       return autoDeleteDays

########################################################################################################################################

def check_time_based_book(pps_port,protocol,pps_host,householdid,timeout,programstarttimeiniso,starttimeinepoch,printflg, contentPlaybackURI=False):
    """
    Check the bookingType is TIME based and the content should be in booked or recording state

    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :param programstarttimeiniso:
    :param starttimeinepoch:
    :param printflg:
    :return:
    """
    try:
       booking_catalog = fetch_bookingCatalog(pps_port,protocol,pps_host,householdid,timeout)
       uri = None
       program_duration = None
       pgm_start_waiTime = None
       contentPlaybackURI = None
       state_book = 0
       if booking_catalog:
           booking_content = json.loads(booking_catalog.content)
           for items,val in enumerate(booking_content):
               try:
                   if val['bookingType'] == "TIME" :
                       if (val['state'] == "BOOKED" or val['state'] == "RECORDING") and (val['startTime'] == programstarttimeiniso):
                           state_book = state_book + 1
                           uri = val['uri']
                           contentPlaybackURI = val["contentPlayUri"]
                           program_duration = val['duration']
                           starttimeinepoch = starttimeinepoch * 1000
                           pgm_start_waiTime = get_timedifference(starttimeinepoch,printflg)
                           print "start wait time from func", pgm_start_waiTime
                           message_pass = "Event is present in the Booked catalog"
               except:
                   pass
       if state_book:
           print message_pass
           if contentPlaybackURI:
               return ("PASS", message_pass, uri, pgm_start_waiTime, booking_catalog, contentPlaybackURI)
           else:
               return ("PASS", message_pass,uri,pgm_start_waiTime,booking_catalog)
       else:
           message = "Booked event is not present in booking catalog"
           return ("FAIL", message,uri,pgm_start_waiTime,booking_catalog)
    except:
       message = "Error  occurred " + PrintException(True)
       print message
       return ("EXCEPTION_FAILURE", message,uri,pgm_start_waiTime,booking_catalog)

##################################################################################################################################################

def check_time_based_recording(pps_port,protocol,pps_host,householdid,timeout,programstarttimeiniso,endtimeinepoch,printflg):
    """
    Check the bookingType is TIME based and the content should be in recording state

    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :param programstarttimeiniso:
    :param endtimeinepoch:
    :param printflg:
    :return:
    """
    program_duration = None
    pgm_end_waiTime = None
    state_record = 0
    try:
        recording_catalog = fetch_recordingCatalog(pps_port,protocol,pps_host,householdid,timeout)
        if recording_catalog:
            recording_content = json.loads(recording_catalog.content)
        else:
            message = "Recording catalog is empty"
            print message
            return ("FAIL", message,pgm_end_waiTime,recording_catalog)
        for items,val in enumerate(recording_content):
           try:
               if val['bookingType'] == "TIME" :
                   if (val['state'] == "RECORDING") and (val['bookingStartTime'] == programstarttimeiniso):
                       message_pass = "Event is in RECORDING state"
                       state_record = state_record + 1
                       endtimeinepoch = endtimeinepoch * 1000
                       pgm_end_waiTime = get_timedifference(endtimeinepoch,printflg)
           except:
               pass

        if state_record :
            print message_pass
            return ("PASS", message_pass,pgm_end_waiTime,recording_catalog)
        else:
           message = "Booked event is not in RECORDING state"
           print message
           return ("FAIL", message,pgm_end_waiTime,recording_catalog)
    except:
       message = "Error occurred : " + PrintException(True)
       print message
       return ("EXCEPTION_FAILURE", message,pgm_end_waiTime,recording_catalog)

##################################################################################################################################################

def check_time_based_recorded(pps_port,protocol,pps_host,householdid,timeout,programstarttimeiniso,printflg):
    """
    Check the bookingType is TIME based and the content should be in recorded state
    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :param programstarttimeiniso:
    :param printflg:
    :return:
    """
    recorded_catalog = None
    try:
        recorded_catalog = fetch_recordingCatalog(pps_port,protocol,pps_host,householdid,timeout)
        if recorded_catalog:
            recorded_content = json.loads(recorded_catalog.content)
        else:
            message = "Recorded catalog is empty"
            print message
            return ("FAIL", message,recorded_catalog)
        state_record = 0
        for items,val in enumerate(recorded_content):
           try:
               if val['bookingType'] == "TIME" :
                   if (val['state'] == "RECORDED") and (val['bookingStartTime'] == programstarttimeiniso):
                      message_pass = "Event is in RECORDED state"
                      state_record = state_record + 1
           except:
               pass
        if state_record:
            print message_pass
            return ("PASS", message_pass,recorded_catalog)
        else:
           message = "Booked event is not in RECORDED state"
           print message
           return ("FAIL", message,recorded_catalog)
    except:
       message = "Error occurred: " + PrintException(True)
       print message
       return ("EXCEPTION_FAILURE", message,recorded_catalog)

##################################################################################################################################################
def delete_series_Onlyrecordings(port,protocol,pps_host,pps_headers,timeout,contentURI,printflg=False):
    """
    Delete the Recoded and Recording episode of a Series
    :param port:
    :param protocol:
    :param pps_host:
    :param pps_headers:
    :param timeout:
    :param contentURI:
    :param printflg:
    :return:
    """
    url =  protocol + "://" + pps_host + ":" + str(port) + contentURI + "/recurrence/recordings"
    print "Delete PPS recording via %s\n " %url
    r = sendURL ("delete",url,timeout,pps_headers)
    if r is not None :
        if r.status_code != 200:
            print "Series recording deletion Failed via  url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return "FAIL"
        else:
            print "\nSeries Recording deleted successfully"
            printLog("\nStatus Code : %s"%r.status_code,printflg)
            return "PASS"
    else:
        return "FAIL"
##################################################################################################################################################
def update_tims_data (tims_dict,status,message,key_value=None):
    """
    Update the TIMS data with the result passed from the script
    :param tims_dict:
    :param status:
    :param message:
    :param key_value:
    :return:
    """
    for key,val in dict.items(tims_dict):
        for value in key_value :
            if key  == value :
                val[1] = message
                val[2] = status
    return tims_dict

######################################################################################################################################
def do_PPSbooking_TBR_returnresponse(port,protocol,pps_host,householdid,pps_headers,payload,timeout,printflg=False):
    """
    PPS booking for time based recoring with return Response
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param pps_headers:
    :param payload:
    :param timeout:
    :param printflg:
    :return:
    """
    try:
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/bookings"
        print "Pps booking via %s\n " %url
        r = sendURL ("post",url,timeout,pps_headers,payload)
        if r is not None :
            if r.status_code != 201:
                print "Pps Booking Failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
                return ("FAIL",r)
            else:
                printLog("\nStatus Code : %s"%r.status_code,printflg)
                return ("PASS",None)
        else:
            return ("FAIL",None)
    except:
        return ("FAIL",None)
#################################################################################################################################
def set_HouseholdEnabledServices_only(protocol,upm_host,upm_port,householdid,servicelist,upm_headers,timeout):
    """
    Set the Enabled services for a Household which are all in Service list
    :param protocol:
    :param upm_host:
    :param upm_port:
    :param householdid:
    :param servicelist:
    :param upm_headers:
    :param timeout:
    :return:
    """
    try:
        enabledservicepasscount = 0
        url = protocol + "://" + upm_host + ":" + str(upm_port) + "/upm/households/" + householdid + "/enabledServices"
        print "Enable the specific service for household via " + url
        enableservice = sendURL("put",url,timeout,upm_headers,servicelist)
        if enableservice is not None:
            if enableservice.status_code != 200:
                print "Enabling Service for the household failed"
                print enableservice.status_code
                print enableservice.headers
                print enableservice.content
                return "FAIL"
            else:
                enabledservicepasscount += 1
        else:
            print "Error in Enabling the Service"
            return "FAIL"
        if enabledservicepasscount >= 1:
            print "Enabling Services is successful"
            return "PASS"
        else:
            print "Enabling Services failed"
            return "FAIL"
    except:
        print "Error occurred in Deleting the Service" + PrintException(True)
        return "FAIL"
##############################################################################################################################################
def modify_recordingstokeep(protocol,pps_host,port_pps,householdid,recordingstokeep_value,timeout,uri,printflg=False):
    """
    Modify the recording to keep parameter of an episode
    :param protocol:
    :param pps_host:
    :param port_pps:
    :param householdid:
    :param recordingstokeep_value:
    :param timeout:
    :param uri:
    :param printflg:
    :return:
    """
    try :
        recordingstokeep_headers = {
            'Content-Type': 'text/plain'
        }
        url = protocol + "://"+ pps_host + ":" + str(port_pps) + str(uri)+ "/recurrence/recordingsToKeep"
        r = sendURL ("put",url,timeout,recordingstokeep_headers,str(recordingstokeep_value))
        print "Recordings to keep is modified  via URL : ", url
        if r is not None :
            if r.status_code != 200:
                print "Recordings to keep modification failed  via URL %s"%url
                print r.status_code
                print r.headers
                print r.content
                return("FAIL", r)
            else:
                return("PASS", r)
        return("FAIL", None)
    except:
        return("FAIL", None)

#######################################################################################################################

def modify_recordingstokeep_response(protocol,pps_host,port_pps,householdid,recordingstokeep_value,timeout,uri,printflg=False):
    """
    Modify the recording to keep parameter of an episode
    :param protocol:
    :param pps_host:
    :param port_pps:
    :param householdid:
    :param recordingstokeep_value:
    :param timeout:
    :param uri:
    :param printflg:
    :return:
    """
    try :
        recordingstokeep_headers = {
            'Content-Type': 'text/plain'
        }
        url = protocol + "://"+ pps_host + ":" + str(port_pps) + str(uri)+ "/recurrence/recordingsToKeep"
        r = sendURL ("put",url,timeout,recordingstokeep_headers,str(recordingstokeep_value))
        print "Recordings to keep is modified  via URL : ", url
        if r is not None :
            if r.status_code != 200:
                print "Recordings to keep modification failed  via URL %s"%url
                print r.status_code
                print r.headers
                print r.content
                return("FAIL", r)
            else:
                return("PASS", r)
        return("FAIL", r)
    except:
        return("FAIL", None)

########################################################################################################################

def fetch_recordingstokeep(catalogresponse,contentId):
    """
    Get the recordings to keep value of an contentid from the JSON response
    :param catalogresponse:
    :param contentId:
    :return:
    """
    Recordingsto_keep = None
    try:
       event_state = json.loads(catalogresponse.content)
       for val in event_state:
           try:
               if val["scheduleInstance"] == contentId :
                  Recordingsto_keep = val['recordingsToKeep']
           except:
               pass
       return Recordingsto_keep
    except:
       print "Not able to retrieve Recordingsto_keep from the booked catalog"
       return Recordingsto_keep
 ################################################################################################################################################################
def debug_print_log(pps_port,protocol,pps_host,householdid,timeout):
    """
    Print the Household catalog and the Failed catalog
    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :return:
    """
    try:
        response =None
        hh_responses = None
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Script Fetching the Household Booked/Recorded Catalog at " + str(datetime.datetime.utcnow())
        hh_responses = fetch_household_Catalog(pps_port,protocol,pps_host,householdid,timeout)
        if hh_responses: 
            print "Household Booked/Recorded Catalog Response:\n" + json.dumps(json.loads(hh_responses.content),indent=4,sort_keys=False)
            contents = json.loads(hh_responses.content)
            contentId_Dict={}
            try:
                for content in contents:
                    contentId = content['content']['id']+ "~" + content['content']['instanceId']
                    contentId_Dict[contentId]=[content['content']['broadcastDateTime'],content['content']['endAvailability'],content['content']['title'],content['content']['state']]
            except :
                pass
            if contentId_Dict:
                print "Retrived Content ID dict:", contentId_Dict
            else:
                pass
        print "Script Fetching Household Failed Recording Catalog at " + str(datetime.datetime.utcnow())
        response = fetch_failedrecording_catalog(pps_port,protocol,pps_host,householdid,timeout)
        if response :
            print "Household Failed Recording Catalog Response:\n" + json.dumps(json.loads(response.content), indent=4, sort_keys=False)
        else:
            pass
    except:
        PrintException()
    finally:
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
####################################################################################################################################################################
def create_household(protocol, upm_port, householdid, upm_host, hh_headers, hh_create_payload):
    """
    Create a new Household, if the household is not present else it will delete the Household and create it again
    :param protocol:
    :param upm_port:
    :param householdid:
    :param upm_host:
    :param hh_headers:
    :param hh_create_payload:
    :return:
    """
    result = False
    try:
        url = protocol + "://" + upm_host + ":" + \
            str(upm_port) + "/upm/households/" + householdid
        if _household_exists(url):
            print "Household already present: " + url
            del_rslt = delete_household(
                protocol, upm_port, householdid, upm_host)
            if del_rslt:
                hh_result = _household_create(
                    url, hh_create_payload, hh_headers)
                if hh_result:
                    result = True
        else:
            hhrslt = _household_create(url, hh_create_payload, hh_headers)
            if hhrslt:
                result = True
    except:
        result = False
    return result
######################################################################################################################################################################
def _household_create(url, hh_create_payload, hh_headers):
    """
    Actual create household
    :param url:
    :param hh_create_payload:
    :param hh_headers:
    :return:
    """
    print "Create household via " + url
    try:
        r = requests.put(url, data=hh_create_payload,
                         headers=hh_headers, timeout=10)
        if r.status_code != 201:
            print r.status_code
            print r.headers
            print r.content
            result = False
        else:
            result = True
    except:
        result = False
    return result
#####################################################################################################################################################################
def list_comp(list1, list2):

    if (set(list1) == set(list2)):
        return True
    else:
        return False
#####################################################################################################################################################################
def playback_recordedevent(cfg,abspath,test,pps_headers,pps_port,pps_host,prmsupportedflag,proxyhostcheckflag,protocol,rm_host,contentplayback_host,contentplayback_port,proxy_host,proxy_port,contentplayback_url,contentplayuri,recordedtitle,householdid,timeout,printflg,recordedcontentduration=None,recordingstarttime=None,sm_deviceid=None,iterationcounter=0, cleanuphousehold=True):
    """
    Playback the content based on the contentplayuri , recordedtitle , householdid
    This function will download the manifest file and then download a video sample.
    if recordingstarttime is given, it will verify the playback start time.
    :param cfg:
    :param abspath:
    :param test:
    :param pps_headers:
    :param pps_port:
    :param pps_host:
    :param prmsupportedflag:
    :param proxyhostcheckflag:
    :param protocol:
    :param rm_host:
    :param contentplayback_host:
    :param contentplayback_port:
    :param proxy_host:
    :param proxy_port:
    :param contentplayback_url:
    :param contentplayuri:
    :param recordedtitle:
    :param householdid:
    :param timeout:
    :param printflg:
    :param recordedcontentduration:
    :param recordingstarttime:
    :param sm_deviceid:
    :param iterationcounter:
    :param cleanuphousehold:
    :return:
    """
    if recordedtitle and contentplayuri:
        try:
            #Add the recorded title with _ for the Manifest and Video Sample file names
            recordedtitlesplit = recordedtitle.split(" ")
            recordedtitlejoin = '_'.join(recordedtitlesplit)
            smsessionid = None

            #Use the SM Session Method for the playback
            if prmsupportedflag == True:
                sm_host = cfg['sm']['host']
                sm_port = cfg['sm']['port']
                #Set the Variables for Playback of Recorded file
                if sm_deviceid:
                    deviceid = sm_deviceid
                else:
                    deviceid = householdid + "d"
                #Get the contentplaybackurl
                contentplaybacklist = get_contentplaybackurl_withPRM(protocol,sm_host,sm_port,contentplayuri,deviceid,timeout,printflg)
                if contentplaybacklist:
                    smsessionid = contentplaybacklist[0]
                    contentplaybackURL = contentplaybacklist[1]
                    #Get the contentURL
                    if proxyhostcheckflag == True:
                        contentURL = get_contentURL_withPRM(protocol,proxy_host,proxy_port,contentplayback_url,contentplaybackURL,printflg)
                    else:
                        contentURL = get_contentURL_withPRM(protocol,contentplayback_host,contentplayback_port,contentplayback_url,contentplaybackURL,printflg)
                else:
                    message = "Testcase Failed: Unable to fetch contentplaybackurl for the playback"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    return ("FAIL",message)

            #Do the RM CNS API call instead of PRM to get the content ID
            else:
                #Get the ContentID from RM CNS API
                contentId = get_contentID_withoutPRM(protocol,rm_host,contentplayuri,timeout,pps_headers,printflg)
                if contentId:
                    #Get the Content URL using contentID
                    if proxyhostcheckflag == True:
                        contentURL = get_contentURL_withoutPRM(protocol,proxy_host,proxy_port,contentplayback_url,contentId,printflg)
                    else:
                        contentURL = get_contentURL_withoutPRM(protocol,contentplayback_host,contentplayback_port,contentplayback_url,contentId,printflg)
                else:
                    message = "Testcase Failed: Unable to Fetch contentid for the playback"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    return ("FAIL",message)

            #Download the manifest file for that response
            if contentURL:
                print "Download the manifest file via" + contentURL
                manifestfileresponse = sendURL('get',contentURL,timeout,pps_headers)
                if manifestfileresponse is not None:
                    if manifestfileresponse.status_code == 200:
                        if manifestfileresponse.content == "":
                            message = "Testcase Failed: Manifestfile Response is empty"
                            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                            return ("FAIL",message)
                        else:
                            manifestfile = test + str(iterationcounter) + "_" + recordedtitlejoin + "_manifest_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt"
                            with open(manifestfile,'wb') as file1:
                                file1.write(manifestfileresponse.content)
                                file1.close()

                            #Download the video Sample and Verify
                            print "Manifest for the Recorded Content\n" +manifestfileresponse.content
                            manifestfilelocation = os.getcwd() + "/" + manifestfile
                            print "Manifest file for the recorded video saved to "+ manifestfilelocation
                            videoplaybackurl = get_videoplaybackurl(manifestfilelocation,contentURL)
                            if videoplaybackurl:
                                print "Download the Video Sample via" + videoplaybackurl
                            else:
                                message = "Testcase Failed: Unable to download video playback url"
                                debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                return ("FAIL",message)
                            downloadfileresponse = sendURL('get',videoplaybackurl,20,pps_headers)
                            if downloadfileresponse is not None:
                                if downloadfileresponse.status_code == 200:
                                    if downloadfileresponse.content == "":
                                        message = "Testcase Failed: Download file response is empty"
                                        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                        return ("FAIL",message)
                                    else:
                                        downloadfile = test + str(iterationcounter) + "_" + recordedtitlejoin + "_file__" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".ts"
                                        with open(downloadfile,'wb') as file2:
                                            for chunk in downloadfileresponse.iter_content(chunk_size = 1024):
                                                if chunk:
                                                    file2.write(chunk)
                                            file2.close()
                                        downloadfilelocation = os.path.dirname(abspath) + "/" + downloadfile
                                        print "Video Sample File Downloaded at " + downloadfilelocation
                                        #Verify the Size of the Video and complete
                                        statinfo = os.stat(downloadfile)
                                        if statinfo.st_size:
                                            print "Video Sample saved in the same folder with the name " + downloadfile + " with the size of " + str(statinfo.st_size) + " bytes"
                                            if recordedcontentduration and recordingstarttime and prmsupportedflag == False:
                                                contentplaybackstarttime = None
                                                contentplaybackendtime = None
                                                contentplaybackstarttime,contentplaybackendtime = get_contentplaybacktime_withoutPRM(protocol,rm_host,contentplayuri,timeout,pps_headers,printflg)
                                                print "ContentPlayback startTime :",contentplaybackstarttime," ContentPlayback EndTime :",contentplaybackendtime
                                                verifyplaybacktime = verifyplaybackstarttime(recordingstarttime,recordedcontentduration,contentplaybackstarttime,contentplaybackendtime)
                                                if verifyplaybacktime == "PASS":
                                                    print "Playback started and ended properly from where it started recording and ended"
                                                else:
                                                    message = "Testcase Failed: Playback started and ended does not match to the Recording Start and End point"
                                                    return ("FAIL",message)
                                            else:
                                                pass
                                else:
                                    message = "Testcase Failed: Unable to fetch downloadfileresponse contents"
                                    print downloadfileresponse.status_code
                                    print downloadfileresponse.content
                                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                    return ("FAIL",message) 
                            else:
                                message = "Testcase Failed: Unable to fetch downloadfileresponse"
                                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                                return ("FAIL",message)
                    else:
                        message = "Testcase Failed: Unable to fetch Manifest File contents"
                        print manifestfileresponse.status_code
                        print manifestfileresponse.content
                        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                        return ("FAIL",message)
                else:
                    message = "Testcase Failed: Unable to fetch Manifest file"
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    return ("FAIL",message)
            else:
                message = "Testcase Failed: Unable to fetch ContentURL"
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                return ("FAIL",message)

            #Teardown the SM Session
            if prmsupportedflag == True and smsessionid != None and statinfo.st_size:
                sm_host = cfg['sm']['host']
                if teardownsmsession(protocol,sm_host,sm_port,smsessionid,printflg):
                    message = "Testcase Passed: SM Session deleted successfully and cleaned up successfully"
                    if cleanuphousehold:
                        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    return ("PASS",message)
                else:
                    message = "Testcase Failed: Unable to delete SM Session"
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                    return ("FAIL",message)
            elif prmsupportedflag == False and statinfo.st_size:
                message = "Testcase Passed: Event recorded and Played back successfully"
                if cleanuphousehold:
                    cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                return ("PASS",message)
            else:
                message = "Testcase Failed: Unable to get the sessionid or size of the video file"
                cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                return ("FAIL",message)
        except:
            message = "Testcase Failed: Error Occurred in Playback Session: " + PrintException(True)
            cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            return ("FAIL",message)
    else:
        message = "Testcase Failed: Unable to fetch contentplayuri or recordedtitle for playback"
        cleanup_household(cfg,pps_port,protocol,pps_host,householdid,pps_headers,timeout)
        return ("FAIL",message)
#####################################################################################################################


def get_all_eventbased_currentandfuture_contentIddict_bytitle(json_responce,title,serviceparameterlist=[]):
    """
    ** DUPLICATE of get_currentandfuture_contentIddict **
    Get the content id dict based of the current and future event
    :param json_responce:
    :param title:
    :param serviceparameterlist:
    :return:
    """
    contents=json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict={}
    all_contentId_Dict_list = []
    current_id = 0
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if title in value['title']:
                        contentId = value['id'] + "~" + value['instanceId']
                        contentId_Dict.setdefault(contentId,[])
                        endtime_difference = get_timedifference(value['endAvailability'],printflg=False)
                        if (value['broadcastDateTime'] < long(current_time) or value['broadcastDateTime'] > long(current_time))and endtime_difference >= 120 and value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                            current_id = current_id + 1
                            contentStartTime = value['broadcastDateTime']
                            contentEndTime = value['endAvailability']
                            duration = contentEndTime - contentStartTime
                            contentId_Dict[contentId].append(contentStartTime)
                            contentId_Dict[contentId].append(contentEndTime)
                            contentId_Dict[contentId].append(duration)
                            if serviceparameterlist:
                                for serviceparameter in serviceparameterlist:
                                    listparameter = value[serviceparameter]
                                    contentId_Dict[contentId].append(listparameter)
                except:
                       print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                       print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
                       print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                       print "Exception Occurred while getting content Dict"
                       PrintException()
                       return None
    if not bool(contentId_Dict):
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "Content ID Dictionary is empty"
        return None
    else:
        if current_id:
            return(contentId_Dict)
        else:
            return None
######################################################################################################################
def get_all_series_contentIddict_currentandfuture_bytitle(json_responce,title=None,serviceparameterlist=[]):
    """
    ** DUPLICATE of get_series_contentIddict_currentandfuture_bytitle **
    Get the content id of the episode which are in current and future
    :param json_responce:
    :param title:
    :param serviceparameterlist:
    :return:
    """
    contents=json.loads(json_responce.content)['services']
    current_time = calendar.timegm(time.gmtime()) * 1000
    contentId_Dict={}
    current_id = 0
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if value['seriesId'] :
                        if title in value['title']:
                            endtime_difference = get_timedifference(value['endAvailability'],printflg=False)
                            contentId = value['id'] + "~" + value['instanceId']
                            contentId_Dict.setdefault(contentId,[])
                            if (value['broadcastDateTime'] < long(current_time) or value['broadcastDateTime'] > long(current_time))and endtime_difference >= 120 and value['endAvailability'] > long(current_time) and value['cdvrAvailable'] == True:
                                current_id = current_id + 1
                                contentStartTime = value['broadcastDateTime']
                                contentEndTime = value['endAvailability']
                                duration = contentEndTime - contentStartTime
                                contentId_Dict[contentId].append(contentStartTime)
                                contentId_Dict[contentId].append(contentEndTime)
                                contentId_Dict[contentId].append(duration)
                                if serviceparameterlist:
                                    for serviceparameter in serviceparameterlist:
                                        listparameter = value[serviceparameter]
                                        contentId_Dict[contentId].append(listparameter)
                except:
                   pass
    if not bool(contentId_Dict):
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "Content ID Dictionary is empty"
        return None
    else:
        if current_id:
            return(contentId_Dict)
        else:
            return None
#######################################################################################################################
def get_v2p_contentID(v2p_protocol,v2pmasternode,port,headers,timeout,printflg):
   try:
        contentid_list = []
        url = v2p_protocol + "://" + v2pmasternode + ":" + str(port) + "/v2/channellineups"
        print "Get channel linups via " + url
        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                message = "could not Get channel linups for v2p master node: " + v2pmasternode
                message_list.append(message)
                print r.status_code
                print r.headers
                print r.content
            else:
                printLog("\nGet channel linups = " + r.content,printflg)
                responce = json.loads(r.content)
                for value in responce:
                    for source in value['properties']['sources']:
                        contentid = source['contentId']
                        contentid_list.append(contentid)
        if contentid_list : 
             return contentid_list
        else:
             return None
   except: 
          return None

########################################################################################################################
#### COMMON COPY VERIFICATION ######
def verify_common_unique_copy(cfg, pps_host,pps_port,protocol, householdids, contentIds, timeout, fanout=0, verifyfanout=True,common_copy=True):
    """
    Verify the recording is a commnon copy.
    If the same even in a channel is recorded from multiple households and if the even is common copy then only one recording will be done
    and shared by all the households.
    For that common recording the fanout value will be <Number of households-1>
    :param cfg: configuration variable
    :param grid_response: Recorded grid response
    :param householdids: List of household ids
    :param contentIds: List of content ids used for pps boooking
    :param timeout: timeout value
    :param fanout: Maximum fanout value <No of Households - 1>
    :param verifyfanout: Optional - If True the Fanout value will be verified. If False the fanout value will not be verified the calling function
                        should take care of it
    :return:If the fanout value verification is success list of content ids will be returned else False
    """

    try:
        print "### Started Common copy verification ###"
        playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, contentIds, householdids, timeout)
        assert playbackuri_list, "Unable to get the Content Playback URI list"
        print "Playback URI list :", playbackuri_list

        contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
        assert contentidlist, "Unable to get the content Id list"
        print "ContentId list :", contentidlist

        streamidstartendtime_list = get_start_and_end_time(cfg, contentidlist, timeout)
        print "Stream id , Starttime and Endtime List:", streamidstartendtime_list
        assert (streamidstartendtime_list), "Unable to get the start and end time of the contentId list"
        streamid_list = [x[0] for x in streamidstartendtime_list]
        starttimelist = [x[1] for x in streamidstartendtime_list]
        endtimelist = [x[2] for x in streamidstartendtime_list]
        isidlist = [x[3] for x in streamidstartendtime_list]
        batchidlist = [x[4] for x in streamidstartendtime_list]
        streamid = compare_time_list(streamid_list)
        start_time = compare_time_list(starttimelist)
        end_time = compare_time_list(endtimelist)
        isid_list = compare_time_list(isidlist)
        batchid_list = compare_time_list(batchidlist)
        main_list = []
        if ((len(start_time[0]) == len(householdids)) and (len(end_time[0]) == len(householdids)) and (len(streamid[0]) == len(householdids))):
            main_list.append(start_time[0][0])
            main_list.append(end_time[0][0])
        else:
            message = "Length of Starttime or Endtime list is not same as the householdids"
            return False, message
        print "MainList:",main_list
        streamid = streamid[0][0]
        isid =isid_list[0][0]
        batchid =batchid_list[0][0]
        print "StreamId : {0} ISIS : {1} BatchID : {2}".format(streamid,isid,batchid)
        segmentIdList = get_segment_response(cfg, main_list, streamid, timeout)
        #print "Segment ID List:", segmentIdList
        assert segmentIdList, "Unable to get the Segment id list"

        if verifyfanout:
            if verify_FanOut_value(cfg, segmentIdList, isid, timeout,batchid=batchid, maxfanout=fanout,common_copy=common_copy):
                message = "CommonCopy Success -> Fanout value is : ", fanout, " for the conetentId :", contentidlist
                return True, message
            else:
                message = "Fanout value is not as expected"
                return False, message
        else:
            return True, segmentIdList
    except Exception as e:
        return False, str(e)

#####################################################################################################################

def fetch_vod_asset(protocol,host_cmdc,port_cmdc,region,catalogueId,timeout,broadcastDateTime,printflg=False):
    """
    Fetch the VOD asset from the CMDC based on the region.
    :param protocol:
    :param host_cmdc:
    :param port_cmdc:
    :param region:
    :param catalogueId:
    :param timeout:
    :param broadcastDateTime:
    :param printflg:
    :return:
    """
    headers = {
            'Accept': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
                }
    url = protocol + "://" + host_cmdc + ":" + str(port_cmdc) +"/cmdc/content?region="+ str(region) + "&catalogueId=" + str(catalogueId) + "&sort=broadcastDateTime&filter=source~vod&count=255"
    print "cmdcVOD asset fetch via URL : ", url
    r = sendURL("get", url, timeout, headers)
    if r is not None :
        if r.status_code != 200:
            print "VOD asset request fetching failed via url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            if r.content == "[]":
                print "VOD asset Response is empty"
                return None
            else:
                return r
    else:
        print "Not able to fetch VOD asset Response"
        return None
########################################################################################################################


def fetch_reverse_epg(protocol,host_cmdc,port_cmdc,broadcastStartTime,broadcastEndTime,serviceIds,region,catalogueId,timeout,printflg=False):
    """
    Fetch the Reverse EPG based on the Broadcast window and service id
    :param protocol:
    :param host_cmdc:
    :param port_cmdc:
    :param broadcastStartTime:
    :param broadcastEndTime:
    :param serviceIds:
    :param region:
    :param catalogueId:
    :param timeout:
    :param printflg:
    :return:
    """
    headers = {
            'Accept': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
                }
    serviceidlist = ','.join(serviceIds)
    print "Current system time:",datetime.datetime.utcnow()
    url = protocol + "://" + host_cmdc + ":" + str(port_cmdc) +"/cmdc/services/schedule/"+ str(broadcastStartTime) + "~" + str(broadcastEndTime) + "?lang=eng&serviceList=" + serviceidlist + "&count=255&region=" + str(region) + "&catalogueId=" + str(catalogueId)
    print "cmdc reverse EPG fetch via URL : ", url
    r = sendURL ("get",url,timeout,headers)
    if r is not None :
        if r.status_code != 200:
            print "reverse EPG request failed via url %s"%url
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            if r.content == "[]":
                print "reverse EPG Response is empty"
                return None
            else:
                return r
    else:
        print "Not able to fetch reverse EPG Response"
        return None

############################################################################################################################################################

def fetch_cmdc_contentdelivery(protocol,host_cmdc,port_cmdc,region,caSystemId,vodId,vodInstanceId,catalogueId,timeout,offerId,printflg=False):
    """
    Get the cmdc content delivery response to get the physical content id

    :param protocol:
    :param host_cmdc:
    :param port_cmdc:
    :param region:
    :param caSystemId:
    :param vodId:
    :param vodInstanceId:
    :param catalogueId:
    :param timeout:
    :param offerId:
    :param printflg:
    :return:
    """
    headers = {
            'Accept': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
                }
    #url = protocol + "://" + host_cmdc + ":" + str(port_cmdc) +"/cmdc/content/"+ str(vodId) + "/" + str(vodInstanceId) + "/uri?caSystemId=" + caSystemId + "&catalogueId=" + str(catalogueId) + "&region=" + str(region)
    url = protocol + "://" + host_cmdc + ":" + str(port_cmdc) +"/cmdc/content/"+ str(vodId) + "~" + str(vodInstanceId) +"/"+ str(offerId)+"/uri?caSystemId=" + str(caSystemId) + "&catalogueId=" + str(catalogueId) + "&region=" + str(region)
    print "cmdcVOD asset fetch via URL : ", url
    r = sendURL ("get",url,timeout,headers)
    if r is not None :
        if r.status_code != 200:
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            if r.content == "[]":
                print "Content delivery API Response is empty"
                return None
            else:
                return r
    else:
        print "Not able to fetch Content delivery API Response"
        return None
#############################################################################################################################################################
def get_serviceidlist_bytitle_fromgrid(json_responce,title):
    """
    Get the Service id list based on the title from grid JSON Response
    Will return the ServiceID , service equilance key, bradcast time and end availability
    :param json_responce:
    :param title:
    :return:
    """
    contents=json.loads(json_responce.content)['services']
    serviceidlist = []
    current_id = 0
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if title in value['title']:
                        current_id += 1
                        serviceidlist.append(value["serviceId"])
                        serviceidlist.append(value["serviceEquivalenceKey"])
                        serviceidlist.append(value["broadcastDateTime"])
                        serviceidlist.append(value["endAvailability"])
                except:
                       print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                       print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
                       print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                       print "Exception Occurred while getting serviceid list"
                       PrintException()
                       return None
    if not bool(serviceidlist):
        print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
        print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
        print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
        print "ServiceId list is empty"
        return None
    else:
        if current_id:
            return(serviceidlist)
        else:
            return None
#############################################################################################################################################################
def get_serviceidlist_bytitle_fromvod(json_responce,title):
    """
    Get the service id list based on title from the VOD JSON response
    Will return the ServiceID , service equilance key, bradcast time and end availability
    :param json_responce:
    :param title:
    :return:
    """
    try:
        try:
            contents = json.loads(json_responce.content)['services']
            content = contents[0]
        except:
            content = json.loads(json_responce.content)
        serviceidlist = []
        titlelist=[]
        if 'contents' in content:
            for value in content['contents']:
                tmplist=[]
                if title in value['title']:
                    tmplist.append(value["serviceId"])
                    tmplist.append(value["serviceEquivalenceKey"])
                    tmplist.append(value["broadcastDateTime"])
                    tmplist.append(value["endAvailability"])

                titlelist.append(value['title'])
                if tmplist:
                    serviceidlist.append(tmplist)
        
        if serviceidlist:
            print "Content list:",serviceidlist
            return (serviceidlist)
        else:
            print "\n" + "#"*20 + "\n"
            print "Required title : "+title+"\nTitle in Response :"+str(titlelist)
            print "\n" + "#"*20 + "\n"
            return None
    except:
        return None
#############################################################################################################################################################
def verifyandreturnobject_fromresponse(json_responce,title,inputvalue):
    contents=json.loads(json_responce.content)['services']
    serviceidlist = []
    outputvalue = None
    current_id = 0
    for cont in contents:
        if 'contents' in cont:
            for value in cont['contents']:
                try:
                    if title in value['title']:
                        if inputvalue in value:
                            current_id += 1
                            outputvalue = value[inputvalue]
                except:
                       print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                       print "Grid Response\n" + json.dumps(json.loads(json_responce.content),indent=4,sort_keys=False)
                       print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                       print "Exception Occurred while verifying the object in response"
                       PrintException()
                       return ("FAIL",None)
    if current_id and outputvalue:
        print outputvalue
        return("PASS",outputvalue)
    else:
        return ("FAIL",None)
######################################################################################################################
############# PARALLEL PLAYBACK VERIFICATION ####################################
def parallel_playback(q1, cfg,abspath,test,pps_headers,pps_port,pps_host,prmsupportedflag,proxyhostcheckflag,protocol,rm_host,contentplayback_host,contentplayback_port,proxy_host,proxy_port,contentplayback_url,contentplayuri,recordedtitle,householdid,timeout,printflg,counter,cleanuphousehold=False):
    """
    Wrapper to call the playback_recordedevent funciton as a seperate process and get the response.
    :param q1:
    :param cfg:
    :param abspath:
    :param test:
    :param pps_headers:
    :param pps_port:
    :param pps_host:
    :param prmsupportedflag:
    :param proxyhostcheckflag:
    :param protocol:
    :param rm_host:
    :param contentplayback_host:
    :param contentplayback_port:
    :param proxy_host:
    :param proxy_port:
    :param contentplayback_url:
    :param contentplayuri:
    :param recordedtitle:
    :param householdid:
    :param timeout:
    :param printflg:
    :param counter:
    :param cleanuphousehold:
    :return:
    """

    try :
        playback_result1, playback_message = playback_recordedevent(cfg, abspath, test, pps_headers, pps_port, pps_host, prmsupportedflag, proxyhostcheckflag, protocol, rm_host, contentplayback_host, contentplayback_port, proxy_host, proxy_port, contentplayback_url, contentplayuri, recordedtitle, householdid, timeout, printflg,iterationcounter=counter,cleanuphousehold=cleanuphousehold)
        if playback_result1 == "PASS":
            q1.put({householdid:"PASS"})
        else:
            q1.put({householdid: playback_message})
    except:
          pass

###################################################################################

def verify_parallel_playback(cfg, abspath, test, pps_headers, pps_port, pps_host, prmsupportedflag, proxyhostcheckflag, protocol, rm_host, contentplayback_host, contentplayback_port, proxy_host, proxy_port, contentplayback_url, title_contentplayuri_dict, timeout, printflg,cleanuphousehold=True):
    """
    Actual Parallel playback function to create sub process to execute the actual playback.
    Get the response from all the process via Queue
    :param cfg:
    :param abspath:
    :param test:
    :param pps_headers:
    :param pps_port:
    :param pps_host:
    :param prmsupportedflag:
    :param proxyhostcheckflag:
    :param protocol:
    :param rm_host:
    :param contentplayback_host:
    :param contentplayback_port:
    :param proxy_host:
    :param proxy_port:
    :param contentplayback_url:
    :param title_contentplayuri_dict:
    :param timeout:
    :param printflg:
    :param cleanuphousehold:
    :return:
    """
    resultQ = []
    try :
        q1 = mpq()
        processess = None
        print "Parallel Execution started :", str(datetime.datetime.now())
        processess = [Process(target=parallel_playback, args=(q1, cfg, abspath, test, pps_headers, pps_port, pps_host, prmsupportedflag, proxyhostcheckflag, protocol, rm_host, contentplayback_host, contentplayback_port, proxy_host, proxy_port, contentplayback_url, title_contentplayuri_dict[householdid][1], title_contentplayuri_dict[householdid][0], householdid, timeout, printflg, i,cleanuphousehold,)) for i, householdid in enumerate(title_contentplayuri_dict)]
        for p in processess:
            p.start()
        for p in processess:
            p.join()
            resultQ.append(q1.get())
        print "Parallel Execution ended :", str(datetime.datetime.now())
        print "Result Queue :",resultQ
        return resultQ
    except:
        return resultQ


###################################################################################
def stop_delete_series_recurrence(port, protocol, pps_host, contentURI,timeout, printflg = False):
    """
    Funciton will Stop the on-going recording of an episode in a series and completely delete the Series
    :param port:
    :param protocol:
    :param pps_host:
    :param contentURI:
    :param timeout:
    :param printflg:
    :return:
    """

    payload = """stateToDelete=BOOKED&stateToDelete=RECORDING&stateToDelete=RECORDED&stopBookingNewEpisodes=true"""

    headers = {
        'Content-Type':'application/x-www-form-urlencoded',
        }
    url = protocol + "://" + pps_host + ":" + str(port) +contentURI+"/recurrence/management"
    print "Stop the series recurrence via : %s\n " % url
    r = sendURL("post", url, timeout, headers,payload)
    if r is not None:
        if r.status_code != 200:
            print r.status_code
            print r.headers
            print r.content
            return "FAIL"
        else:
            print "Series recurrence stopped successfully\n"
            printLog("Status Code : %s" % r.status_code, printflg)
            return "PASS"
    else:
        return "FAIL"
#####################################################################################
def get_vmr_response(cfg, contentid, timeout):
    try:
        protocol = cfg['protocol']
        vmr_host = cfg['vmr']['host']
        vmr_port = cfg['vmr']['port']
        headers = {
            'content-type': 'application/json',
            'Accept': 'application/json',
            'Source-Type': 'SMS',
            'Source-Id': '123'
        }
        url = protocol + "://" + vmr_host + ":" + str(vmr_port) + "/api/findxrid/" + contentid
        print "\nURL to get the vmr response:", url
        r = sendURL("get", url, timeout, headers)
        if r is not None:
            if r.status_code != 200:
                print "Unable to get vmr response with URL :", url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                return r
        else:
             print "Not able to fetch vmr Response"
             return None
    except Exception as e:
        print "Exception in get vmr response  :", str(e)
        return None
####################################################################################################
def verify_vmr_response_status(cfg, pps_host,pps_port,protocol, householdids, contentIds, timeout):
    """
    Fetch the VMR reponse based on the contentid and verify the Status is Complete
    :param cfg:
    :param pps_host:
    :param pps_port:
    :param protocol:
    :param householdids:
    :param contentIds:
    :param timeout:
    :return:
    """
    try:
        Status = None
        vmr_response = []
        print "### Started VMR verification ###"
        if not isinstance(contentIds, list):
            contentIds = [contentIds]
        if not isinstance(householdids, list):
            householdids = [householdids]
        playbackuri_list = get_content_playbackURI(pps_host, pps_port, protocol, contentIds, householdids, timeout)
        assert playbackuri_list, "Unable to get the Content Playback URI list"
        print "Playback URI list :", playbackuri_list
        contentidlist = get_contentid_from_recid(cfg, playbackuri_list, timeout)
        assert contentidlist, "Unable to get the content Id list"
        print "ContentId list :", contentidlist
        vmr_response = get_vmr_response(cfg,contentidlist[0], timeout)
        assert (vmr_response), "Unable to get the vmr response of the contentId list"
        jsonresponse = json.loads(vmr_response.content)
        print "JSON response :", vmr_response.content
        for item in jsonresponse:
            Status = item["Status"]
        if Status == "COMPLETE":
            return True, vmr_response
        else:
            return False, vmr_response
    except Exception as e:
        return False, e
######################################################################################################


def playback_event_with_contentid(cfg, abspath, test, rm_headers, content_id, playback_title, timeout, print_flg):
    """
    Playback the event based on the content id from the RM response.
    :param cfg: Complete configuration variable
    :param abspath: path to store the manifest and the .ts file
    :param test: test case name
    :param rm_headers:Headers to download the manifest file
    :param content_id: Content id to form the content url to download the manifestfile.
    :param playback_title: event title to form the manifest file.
    :param timeout: timeout value in seconds
    :param print_flg: flag to print the log
    :return: PASS , <message> if success else FAIL, <message>
    """

    try:
        proxyhostcheckflag = cfg['proxyHostNeeded']
        protocol = cfg['protocol']
        contentplayback_host = cfg['contentplayback']['host']
        contentplayback_port = cfg['contentplayback']['port']
        contentplayback_url = cfg['contentplayback']['url']
        proxy_host = cfg['proxyhost']['host']
        proxy_port = cfg['proxyhost']['port']


        # Get the Content URL using contentID
        if proxyhostcheckflag == True:
            contentURL = get_contentURL_withoutPRM(protocol, proxy_host, proxy_port, contentplayback_url, content_id,
                                                   print_flg)
        else:
            contentURL = get_contentURL_withoutPRM(protocol, contentplayback_host, contentplayback_port,
                                                   contentplayback_url, content_id, print_flg)

        # Download the manifest file for that response
        if contentURL:
            print "Download the manifest file via " + contentURL
            manifestfileresponse = sendURL('get', contentURL, timeout, rm_headers)
            if manifestfileresponse is not None:
                if manifestfileresponse.status_code == 200:
                    if manifestfileresponse.content == "":
                        message = "TestCase Failed: Manifestfile Response is empty"
                        return "FAIL", message
                    else:
                        manifestfile = test + "_" + playback_title + "_manifest_" + datetime.datetime.now().strftime(
                            "%Y%m%d-%H%M%S") + ".txt"
                        with open(manifestfile, 'wb') as file1:
                            file1.write(manifestfileresponse.content)
                            file1.close()

                        # Download the video Sample and Verify
                        print "Manifest for the Recorded Content\n" + manifestfileresponse.content
                        manifestfilelocation = os.getcwd() + "/" + manifestfile
                        print "Manifest file for the recorded video saved to " + manifestfilelocation
                        videoplaybackurl = get_videoplaybackurl(manifestfilelocation, contentURL)
                        if videoplaybackurl:
                            print "Download the Video Sample via" + videoplaybackurl
                        else:
                            print "contentURL :", contentURL
                            message = "TestCase Failed: Unable to download video playback url"
                            return "FAIL", message
                        downloadfileresponse = sendURL('get', videoplaybackurl, 20, rm_headers)
                        if downloadfileresponse is not None:
                            if downloadfileresponse.status_code == 200:
                                if downloadfileresponse.content == "":
                                    message = "TestCase Failed: Download file response is empty"
                                    return "FAIL", message
                                else:
                                    downloadfile = test + "_" + playback_title + "_file__" + \
                                                   datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".ts"
                                    with open(downloadfile, 'wb') as file2:
                                        for chunk in downloadfileresponse.iter_content(chunk_size=1024):
                                            if chunk:
                                                file2.write(chunk)
                                        file2.close()
                                    downloadfilelocation = os.path.dirname(abspath) + "/" + downloadfile
                                    print "Video Sample File Downloaded at " + downloadfilelocation
                                    # Verify the Size of the Video and complete
                                    statinfo = os.stat(downloadfile)
                                    if statinfo.st_size:
                                        message = "Video Sample saved in the same folder with the name " + \
                                                  downloadfile + " with the size of " + str(statinfo.st_size) + " bytes"
                                        return "PASS", message
                            else:
                                message = "TestCase Failed: Unable to fetch download fileresponse contents"
                                print downloadfileresponse.status_code
                                print downloadfileresponse.content
                                return "FAIL", message
                        else:
                            message = "TestCase Failed: Unable to download video file"
                            return "FAIL", message
                else:
                    message = "TestCase Failed: Unable to fetch Manifest File contents"
                    print manifestfileresponse.status_code
                    print manifestfileresponse.content
                    return "FAIL", message
            else:
                message = "TestCase Failed: Unable to fetch Manifest file"
                return "FAIL", message
        else:
            message = "TestCase Failed: Unable to fetch ContentURL"
            return "FAIL", message

    except:
        message = "TestCase Failed: Error Occurred in Playback Session"
        PrintException(True)
        return "FAIL", message

############################################################################################################

def book_and_verify(pps_port, protocol, pps_host, householdid, pps_headers, payload, contentid, contentid_list=None, catalog_fetch_delay=2, timeout=2):
    """
    Function to book the content and verify the content is in booking state.
    It works for both the event and the series.
    In case of event just pass the content id
    In case of series pass the contentId of the episode to book and contentId_List of episodes to verify
    :param pps_port: PPS Port
    :param protocol: PPS protocol
    :param pps_host: PPS Host
    :param householdid: Household ID
    :param pps_headers: PPS header for booking
    :param payload: PPS payload for booking either event / series
    :param contentid: Content id to be booked
    :param contentid_list: List of content ID to be verified for booking state
    :param catalog_fetch_delay: delay before verifying the booking
    :param timeout:default timeout
    :return: tuple of PASS / FAIL and message
    """
    try:
        result = do_PPSbooking(pps_port, protocol, pps_host, householdid, pps_headers, payload, contentid, timeout)
        if result == "PASS":
            time.sleep(catalog_fetch_delay)
            if not contentid_list:
                contentid_list = [contentid]
            verify_book, responce = verify_booking(pps_port, protocol, pps_host, householdid, contentid_list, timeout)
            if verify_book == 'PASS':
                return ("PASS", responce)
            else:
                message = " Testcase Failed : Unable to Verify Booked Catalog"
                return ("FAIL", message)
        else:
            message = "Testcase Failed : PPS Booking failed for the contentId %s" % (contentid)
            return ("FAIL", message)
    except:
        message = "Testcase Failed : Error occured in Script: " + PrintException(True)
        return ("FAIL", message)
##############################################################################################################

def record_and_verify(pps_port, protocol, pps_host, householdid, content_id, endTime, recording_to_recorded_delay, content_id_list = None, timeout = 2, printflg = True):
    """
    Funciton to verify the event is in recording state and after the end Availability verify the event is in recorded state.
    :param pps_port: PPS Port
    :param protocol: Protocol
    :param pps_host: PPS Host
    :param householdid: HouseholdId
    :param content_id: Content Id to be verified
    :param endTime: End time of the event to complete recording
    :param recording_to_recorded_delay: Delay in seconds for recording to recorded state change
    :param content_id_list: Content ID list to be verified
    :param timeout: Default timeout value
    :param printflg: Print flag
    :return:
    """
    try:
        result_recording, responce_recording = verify_recording_state(pps_port, protocol, pps_host, householdid, content_id, timeout)
        if result_recording == "PASS":
            program_end_waittime = get_timedifference(endTime, printflg)
            print "script will wait for ", str(program_end_waittime), " seconds for recording to complete"
            time.sleep(program_end_waittime)
        else:
            message = "TestCase Failed : Unable to Verify Recording Catalog"
            return ("FAIL", message)
        time.sleep(recording_to_recorded_delay)
        if not content_id_list:
            content_id_list = [content_id]
        result_recorded, responce_recorded = verify_recorded_state(pps_port, protocol, pps_host, householdid, content_id_list, timeout)
        if result_recorded == "PASS":
            return ("PASS", responce_recorded)
        else:
            message = "TestCase Failed : Unable to Verify Recorded Catalog"
            return ("FAIL", message)
    except:
        message = "TestCase Failed : Error occured in Script: " + PrintException(True)
        return ("FAIL", message)

###################################################################################################################################

def household_status(cfg, householdid, payload, timeout):
    """
    Funcition to suspend or activate the household
    :param cfg: Config parameter
    :param householdid: household id to be suspended or activated
    :parm payload : "SUSPENDED" / "ACTIVATED"
    :param timeout: timeout value
    :return: True if the household is suspended else False
    """

    try:
        protocol = cfg['protocol']
        upm_port = cfg['upm']['port']
        upm_host = cfg['upm']['host']

        #curl -s -vk -w "\n" -H "Accept: application/json" -H "Source-Type: BBS" -H "Source-ID: 127.0.0.1" -H "Content-Type: text/plain" -d "SUSPENDED" -X PUT "http://211.208.185.9:6040/upm/households/RAJA0/householdStatus"

        headers = {
            "Accept": "application/json",
            "Source-Type": "BBS",
            "Source-ID": "127.0.0.1",
            "Content-Type": "text/plain"
        }

        url = protocol + "://" + upm_host + ":" + str(upm_port) + "/upm/households/"+householdid+"/householdStatus"

        r = sendURL("put", url, timeout, headers, payload)
        if r is not None:
            if r.status_code != 200:
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
                return False
            else:
                state = json.loads(r.text)['value']
                print "Household %s is in State %s " % (householdid, state)
                return r
        return False

    except Exception as e:
        print "Error in household_activate_suspend : ", str(e)
        return False


####################################################################################################################
def activate_household(cfg, householdid, timeout):
    """
    Funciton to activate the household passed
    :param cfg: Configuration file
    :param householdid: Household Id to be Activated
    :param timeout: timeout value
    :return: True if the household is Activated state else False
    """
    household_state = household_status(cfg, householdid, "ACTIVATED", timeout)
    if json.loads(household_state.text)['value'] == "ACTIVATED":
        print "Household %s is in ACTIVATED state" %householdid
        return True
    else:
        print "Household %s is not in AVTIVATED state" %householdid
        print household_state
        return False


####################################################################################################################
def suspend_household(cfg, householdid, timeout):
    """
    Function to suspend the household
    :param cfg: configuration variable
    :param household: Household to be suspended
    :param timeout: timeout value
    :return: True if the household is Suspended else False
    """
    household_state = household_status(cfg, householdid, "SUSPENDED", timeout)
    if json.loads(household_state.text)['value'] == "SUSPENDED":
        print "Household %s is in SUSPENDED state" %householdid
        return True
    else:
        print "Household %s is not in SUSPENDED state" %householdid
        print household_state
        return False

######################################################################################################################
def verify_channel_bookedcatalog(pps_port,protocol,pps_host,householdid,contentid_list,channel,timeout):
    """
        Function to verify the list of events and the channel is present in the booked catalog as passed
        :param pps_port: PPS Port
        :param protocol: Protocol
        :param pps_host: PPS Host
        :param householdid: HouseholdId
        :param contentid_list: Content ID list to be verified
        :param channel: Channel to be verified
        :param timeout: Default timeout value
        :return:
    """
    try:
        count_contentId = 0
        contentId_list = []
        if isinstance(contentid_list,list):
           contentId_list = contentid_list
        else :
           contentId_list = [contentid_list]
        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/households/" + str(householdid) + "/bookings"
        print "get all Bookings by:  %s\n " % url
        r = sendURL("get", url, timeout)
        if r is not None:
            if r.status_code != 200:
                print "Fetching Booking Catalog Failed via  url %s" % url
                print r.status_code
                print r.headers
                print r.content
                return ("FAIL",None)
            else:
                if r.content == "[]":
                    failedrecordingcatalog = fetch_failedrecording_catalog(pps_port,protocol,pps_host,householdid,timeout)
                    if failedrecordingcatalog:
                        failedrecordingcontent = json.loads(failedrecordingcatalog.content)
                        for temp in contentId_list:
                            for val in failedrecordingcontent:
                                try:
                                    if val["scheduleInstance"] == temp:
                                         print "Booking Catalog is empty but the event is in Failed State"
                                         return ("FAIL", None)
                                except:
                                    pass
                    else:
                        message = "Booked Catalog and Failed Recording catalog is empty which means Event is not present" \
                                  "in Booked Catalog"
                        return ("FAIL", message)
                else:
                    event_state = json.loads(r.content)
                    for temp in contentId_list:
                        for val in event_state:
                            try:
                                if val["scheduleInstance"] == temp:
                                    if (val['state'] == "BOOKED") and (val['channelId'] == channel):
                                        count_contentId += 1
                            except:
                                pass
        else:
            print "Not able to fetch the Booking Catalog"
            return ("FAIL", None)
        if count_contentId == len(contentId_list):
            print "All programs with the contentids %s is in BOOKED state" %contentId_list
            return ("PASS",r)
        else:
            message = "All programs with the contentids %s is not in BOOKED state" %contentId_list
            print message
            return ("FAIL", message)
    except:
        print "Error  occurred " + PrintException(True)
        return ("EXCEPTION_FAILURE",None)

###########################################################################################################################

def verify_channel_recordedcatalog(pps_port,protocol,pps_host,householdid,contentid_list,channel,timeout):
    """
        Function to verify the list of events and the channel is present in the recorded catalog as passed
        :param pps_port: PPS Port
        :param protocol: Protocol
        :param pps_host: PPS Host
        :param householdid: HouseholdId
        :param contentid_list: Content ID list to be verified
        :param channel: Channel to be verified
        :param timeout: Default timeout value
        :return:
    """
    try:
        count_contentId = 0
        contentId_list = []
        if isinstance(contentid_list,list):
           contentId_list = contentid_list
        else :
           contentId_list = [contentid_list]
        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/households/" + str(householdid) + "/recordings"
        print "get all Recordings by:  %s\n " % url
        r = sendURL("get", url, timeout)
        if r is not None:
            if r.status_code != 200:
                print "Fetching Recording Catalog Failed via  url %s" % url
                print r.status_code
                print r.headers
                print r.content
                return ("FAIL",None)
            else:
                if r.content == "[]":
                    failedrecordingcatalog = fetch_failedrecording_catalog(pps_port,protocol,pps_host,householdid,timeout)
                    if failedrecordingcatalog:
                        failedrecordingcontent = json.loads(failedrecordingcatalog.content)
                        for temp in contentId_list:
                            for val in failedrecordingcontent:
                                try:
                                    if val["scheduleInstance"] == temp:
                                         print "Recording Catalog is empty but the event is in Failed State"
                                         return ("FAIL", None)
                                except:
                                    pass
                    else:
                        message = "Recording Catalog and Failed Recording catalog is empty which means Event is not present" \
                                  "in Recording Catalog"
                        return ("FAIL", message)
                else:
                    event_state = json.loads(r.content)
                    for temp in contentId_list:
                        for val in event_state:
                            try:
                                if val["scheduleInstance"] == temp:
                                    if (val['state'] == "RECORDED") and (val['channelId'] == channel):
                                        count_contentId += 1
                            except:
                                pass
        else:
            print "Not able to fetch the Recording Catalog"
            return ("FAIL", None)
        if count_contentId == len(contentId_list):
            print "All programs with the contentids %s is in RECORDED state" %contentId_list
            return ("PASS",r)
        else:
            message = "All programs with the contentids %s is not in RECORDED state" %contentId_list
            print message
            return ("FAIL",message)
    except:
        print "Error  occurred " + PrintException(True)
        return ("EXCEPTION_FAILURE",None)

###########################################################################################################################
def get_copyType(cfg, scheduleid, serviceEqKey, startTime, endTime, timeout):
    """
    Fetch copy type for an event based on the below parameters
    :param cfg:
    :param scheduleid:
    :param serviceEqKey:
    :param startTime:
    :param endTime:
    :param timeout:
    :return:
    """
    protocol = cfg['protocol']
    ipom_port = cfg['ipom']['port']
    ipom_host = cfg['ipom']['host']
    headers = {
            'Accept': 'application/json'
                }
    url = protocol + "://" + ipom_host + ":" + str(ipom_port) + "/content/policies?contentId=" + str(scheduleid) + \
          "&serviceEquivalenceKey=" + str(serviceEqKey) \
          + "&SDT=" + str(startTime) + "&EDT=" + str(endTime)

    print "get CopyType by:  %s\n " % url
    print "Current system time while copyType of the particular event " + str(datetime.datetime.utcnow())
    r = sendURL("get", url, timeout)

    if r is not None:
        if r.status_code != 200:
            print "Fetching CopyType Catalog Failed via  url %s" % url
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            if r.content == "[]":
                print "copyType Catalog is empty"
                return None
            else:
                print "Catalog Response\n" + json.dumps(json.loads(r.content), indent=4, sort_keys=False)
                return r
    else:
        print "Not able to fetch the copyType Catalog"
        return None
##########################################################################################################
def booked_episodes_parentGroupID(series_Id,event_state):
    """
    Get the details about the episode in a series based on the series id from the JSON response
    :param series_Id:
    :param event_state:
    :return:
    """
    event_state = json.loads(event_state.content)
    print "Series Id:",series_Id
    seriesdict ={}
    episodeNumberdisct={}
    if isinstance(event_state,list):
        for val in event_state:
            try:
                if val['seriesId'] == series_Id:
                   episodeNumber = str(val['title'])[-1]
                   seriesdict.setdefault(episodeNumber,[])
                   contentStartTime = iso2epoch(val['bookingStartTime'])
                   duration = isotimetoseconds(val['duration'])
                   contentEndTime = contentStartTime + duration
                   recordingId = val['recordingId']
                   booking_uri = val['uri']
                   booking_title= val['title']
                   contentId = val['scheduleInstance']
                   seriesId = val['seriesId']
                   seriesdict[episodeNumber].append(contentStartTime)
                   seriesdict[episodeNumber].append(contentEndTime)
                   seriesdict[episodeNumber].append(duration)
                   seriesdict[episodeNumber].append(recordingId)
                   seriesdict[episodeNumber].append(booking_uri)
                   seriesdict[episodeNumber].append(booking_title)
                   seriesdict[episodeNumber].append(contentId)
                   seriesdict[episodeNumber].append(seriesId)
                   (episodeNumberdisct.setdefault(episodeNumber,[])).extend(seriesdict.get(episodeNumber))
            except Exception as e:
                pass
    if episodeNumberdisct :
        return(episodeNumberdisct)
    else:
        print "Error in retrieving booked episodes"
        return None
#############################################################################################################

def get_contentid_state(pps_port, protocol, pps_host, householdid, random_contentId_list, timeout):
    """
    Get the State of and content whether it is in Booked / Recording / Recorded / Failed state
    :param pps_port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param random_contentId_list:
    :param timeout:
    :return:
    """
    try:
        contentId_list = []
        if isinstance(random_contentId_list,list):
            contentId_list = random_contentId_list
        else:
            contentId_list = [random_contentId_list]

        r = None
        state_dict = {}
        r = fetch_Catalog(pps_port, protocol, pps_host, householdid, timeout)
        if r is not None:
            event_state = json.loads(r.content)
            for temp in contentId_list:
                for val in event_state:
                    try:
                        if val["scheduleInstance"] == temp:
                            state_dict.setdefault(temp, [])
                            state_dict[temp].append(val['state'])
                    except:
                        pass

            if len(state_dict) < len(random_contentId_list):
                r = fetch_failedrecording_catalog(pps_port, protocol, pps_host, householdid, timeout)
                if r is not None:
                    event_state = json.loads(r.content)
                    for temp in contentId_list:
                        for val in event_state:
                            try:
                                if val["scheduleInstance"] == temp:
                                    state_dict.setdefault(temp, [])
                                    state_dict[temp].append(val['state'])
                            except:
                                pass
        else:
            print "PPS Catalog is empty"
            return "FAIL", None

        return state_dict, r
    except:
        print "Error  occurred " + PrintException(True)
        return "EXCEPTION_FAILURE", None

###################################################################################################################


def _input(msg, q):
    """
    Thread to get the raw input from user and returns it.
    :param msg:
    :param q:
    :return:
    """
    ra = raw_input(msg)
    if ra:
        q.put(ra)
    else:
        q.put("None")
    return

def _slp(tm, q):
    """
    Thread to wait for a maximum time
    :param tm:
    :param q:
    :return:
    """
    time.sleep(tm)
    q.put("Timeout")
    return

def wait_for_input(msg="Press Enter Once Done", time=10):
    """
    Wait for an input from the used for the max time specified in the time argument.
    :param msg:
    :param time:
    :return:
    """
    q = Queue.Queue()
    th = threading.Thread(target=_input, args=(msg, q,))
    tt = threading.Thread(target=_slp, args=(time, q,))

    th.start()
    tt.start()
    ret = None
    while True:
        ret = q.get()
        if ret:
            th._Thread__stop()
            tt._Thread__stop()
            return ret
    return ret

#######################################################################################################################

def get_eventPolicy(cfg , timeout):
    """
    Fetch the policy from the IPOM based on the time window
    :param cfg:
    :param timeout:
    :return:
    """
    protocol = cfg['protocol']
    ipom_port = cfg['ipom']['port']
    ipom_host = cfg['ipom']['host']
    timewindows = epochtime(2)
    headers = {
            'Accept': 'application/json'
                }
    url = protocol + "://" + ipom_host + ":" + str(ipom_port) + "/events/policies?window=" + timewindows

    print "get eventPolicy by:  %s\n " % url
    print "Current system time while event Policy " + str(time.time())
    r = sendURL("get", url, timeout)

    if r is not None:
        if r.status_code != 200:
            print "Fetching eventPolicy Failed via  url %s" % url
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            if r.content == "[]":
                print "eventPolicy  is empty"
                return None
            else:
                print "eventPolicy Response\n" + json.dumps(json.loads(r.content), indent=4, sort_keys=False)
                return r
    else:
        print "Not able to fetch the eventPolicy"
        return None


#########################################################################################################################
def fetch_bookedlibrary_timeframe(protocol,pps_host,pps_port,householdid,pps_headers,starttimeinepoch,endtimeinepoch,timeout):
    """
        Return the content id in booked state in specified time window
        :param pps_port: PPS Port
        :param protocol: Protocol
        :param pps_host: PPS Host
        :param householdid: HouseholdId
        :param starttimeinepoch: starttime of the timeframe in question on booking list
        :param endtimeinepoch: endtime of the timeframe in question on booking list
        :param timeout: Default timeout value
        :return:
    """
    try:
        starttimeiniso = epoch2iso(starttimeinepoch)
        endtimeiniso = epoch2iso(endtimeinepoch)
        url = protocol + "://"+ pps_host + ":" + str(pps_port) +"/pps/households/"+ str(householdid) \
              + "/bookings?filter:startTime=(" + starttimeiniso + "," + endtimeiniso + ")"
        r = sendURL ("get",url,timeout,pps_headers)
        print "Booked library for the timeframe fetched  via URL : ", url
        if r is not None :
            if r.status_code != 200:
                print "Booked library fetch via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
                return ("FAIL", r)
            else:
                if r.content == "[]":
                    print "Booked Library is empty"
                    return ("FAIL", None)
                else:
                    return ("PASS", r)
        else:
            print "Unable to fetch the booked catalog in timeframe"
            return ("FAIL", None)
    except:
        message = "Error Occurred:" + PrintException(True)
        print message
        return ("EXCEPTION_FAILURE", message)

###########################################################################################################################

def verify_contentid_response(response, contentidlist):
    """
        Verify the contentids are present in the JSON response
        :param response: Response which needs to parse
        :param contentidlist: List of contentids which needs to check in the response
        :return:
    """
    try:
        counter = 0
        responsecontent = json.loads(response.content)
        try:
            for items in responsecontent:
                for contentid in contentidlist:
                    if items["scheduleInstance"] == contentid:
                        counter += 1
        except:
            pass
        if counter == len(contentidlist):
            return "PASS"
        else:
            return "FAIL"
    except:
        message = "Error Occurred:" + PrintException(True)
        print message
        return message

###########################################################################################################################

def verify_response_starttime(response, starttimeinepoch, endtimeinepoch):
    """
        :param response: get the response which needs to parse
        :param starttimeinepoch: get the starttime of program in epoch
        :param endtimeinepoch: get the endtime of program in epoch
        :return:
    """
    try:
        responsecontent = json.loads(response.content)
        programstarttimelist = []
        for items in responsecontent:
            try:
                if items['startTime']:
                    bookingstarttimeinepoch = iso2epoch(items['startTime'])
                    programstarttimelist.append(bookingstarttimeinepoch)
            except:
                pass
        print "Starttime list from the booking list within timeframe %s" %programstarttimelist
        if (min(programstarttimelist) >= starttimeinepoch) and (max(programstarttimelist) <= endtimeinepoch):
            return "PASS"
        else:
            return "FAIL"
    except:
        message = "Error Occurred:" + PrintException(True)
        print message
        return message
######################################################################################################################

def rebroadcast_episode(path, showID = None, episode = None, startTime = None):
    """
    Function to generete a rebrodcast episode XML from the ingested XML
    :param path: Ingested XML path
    :param showID:
    :param episode:
    :param startTime:
    :return:
    """

    try:
        postfile = "rebroadcast_"+showID+".xml"
        if not os.path.exists(path):
            print "File not present :",path
            return False
        with open(path, 'r') as xmlfile_i:
            lines = [line for line in xmlfile_i if line.strip() is not ""]
        xmlfile_i.close()

        with open('tmpxml.xml', "w") as xmlfile_o:
            line1, last_line = lines[1], lines[-1]
            del lines[1], lines[-1]
            xmlfile_o.writelines(lines)
        xmlfile_o.close()

        last_line = '\n' + last_line
        tree = ET.parse('tmpxml.xml')
        root = tree.getroot()

        rt = root.findall(".//ChannelDayScheduleItem")

        if not isinstance(episode, list):
            to_be_rebroadcast = [showID+"_1_"+str(episode)]
        else:
            to_be_rebroadcast = [showID+"_1_"+str(ep) for ep in episode]

        print "\nEpisode to rebroadcast :", to_be_rebroadcast

        # Remove the unwanted episodes
        ep_to_keep = []
        for ep_to_rebroadcast in to_be_rebroadcast:
            for ep in rt:
                if ep_to_rebroadcast in ep.find('id').text:
                    ep_to_keep.append(ep)

        for ep in rt:
            if ep not in ep_to_keep:
                root.remove(ep)

        duration = 0
        # Modify the rebroadcast episode
        for ep_to_rebroadcast in to_be_rebroadcast:
            for ep in rt:
                if ep_to_rebroadcast in ep.find('id').text:
                    try:
                        print "\nRebroadcasting the episode : ", ep.find('id').text
                        tempid = (ep.find('id').text).split('_')
                        id = int(tempid[-1])+100
                        newid = '_'.join(tempid[:-1])+"_"+str(id)
                        print "New Id :", newid
                        # Update the ID tag
                        ep.find('id').text = newid
                        title_id = '_'.join(tempid[:-1])+"_"+str(id+1)
                        title_key = '_'.join(tempid[:-1])+"_"+str(id+2)

                        # Update the ID tag under TITLE
                        ep.find('title').find('id').text = title_id

                        # Update the KEY tag under TITLE
                        ep.find('title').find('key').text = title_key

                        startTime_source = ep.find('title').find('startDateTime').text
                        endtime_source = ep.find('title').find('endDateTime').text

                        print "Original Episode Timing :", startTime_source, " To :", endtime_source

                        startTime_source = iso2epoch(startTime_source)
                        endtime_source = iso2epoch(endtime_source)

                        # If rebroadcasting 2 episodes then the seconds episode start time has to be after the first
                        startTimeepoc = iso2epoch(startTime) + duration

                        duration = endtime_source - startTime_source

                        print "Duration :", duration

                        startTime = epoch2iso(startTimeepoc)
                        print "Post Time :", startTime
                        #startTimeepoc = iso2epoch(startTime)
                        newEndTimeepoc = startTimeepoc + duration
                        newEndTime = epoch2iso(newEndTimeepoc)
                        print "End Availability :", newEndTime

                        # Update the ID tag under ChannelDaySchedule
                        endtimestamp = time.strftime("%d%m%Y%H%M%S", time.gmtime(newEndTimeepoc))
                        uniqueid = root.find('id').text
                        uniqueid = uniqueid.split('~')
                        new_uniqid = '~'.join(uniqueid[:-1])+"~"+str(endtimestamp)

                        print "New content id :", new_uniqid
                        root.find('id').text = new_uniqid

                        # Update the startDateTime under TITLE
                        ep.find('title').find('startDateTime').text = startTime

                        # Update the endDateTime under TITLE
                        ep.find('title').find('endDateTime').text = newEndTime

                        # Update the startDateTime under InstanceAvailability
                        ep.find('title').find('availability').find('InstanceAvailability').find('startDateTime').text = startTime

                        # Update the endDateTime under InstanceAvailability
                        ep.find('title').find('availability').find('InstanceAvailability').find('endDateTime').text = newEndTime

                        print "Prepared for Rebroadcast :",ep_to_rebroadcast

                    except Exception as e:
                        print "Error in Updating the Value of broadcast episode."
                        print str(e)
                        return False

        tree.write(postfile)
        # Remove the temp file generated
        os.remove('tmpxml.xml')

        # Add the initial and last line retrived earlier
        line0 = '\n<?xml version="1.0" encoding="UTF-8"?>\n'
        with open(postfile, 'rb') as fp:
            rwlines = fp.readlines()
            rwlines.insert(0, line0)
            rwlines.insert(1, line1)
            rwlines.append(last_line)
        fp.close()
        with open(postfile, 'w') as fp1:
            for ele in rwlines:
                fp1.writelines(ele)
            fp1.close()

        print "\nRebroadcast XML file generated :",postfile

        return postfile

    except Exception as e:
        print "Error in rebroadcast_episode function"
        print str(e)
        return False


#######################################################################################################################

def send_xmlFile_CI(xmlFile, cfg):
    """
    Post the XML file generated
    :param xmlFile:
    :param cfg:
    :return:
    """
    host = cfg['ci']['host']
    port = cfg['ci']['port']
    timeout = 10
    header = {
        'Content-Type': 'application/xml',
    }
    file_contents = ''
    uri_command = ''
    uri_id = ''
    file_contents = ''
    # Extract the uri command and uri_id
    with open(xmlFile, 'r') as fptr:
        file_contents = fptr.read()
        file_list = file_contents.split('<url>')
        uri_list = file_list[1].split('</url>')
        file_contents = file_list[0] + uri_list[1]
        uri_id = find_between(file_contents, '<id>', '</id>')
        uri_command = uri_list[0]
    with open(xmlFile, 'w') as fptr:
        fptr.write(file_contents)
    url = 'http://' + str(host) + ':' + str(port) + '/' + str(uri_command) + '/' + str(uri_id)
    with open(xmlFile, 'r') as fptr:
        contents = fptr.read()
        contents = contents.strip()
        r = requests.put(url, headers=header, data=contents, timeout=timeout)
        #print r.status_code
        #print r.headers
        #print r.content
        if r is not None:
            if r.status_code != 200:
                print "error in posting the xml to the CI host via  url %s" % url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                return "PASS"
        else:
            print "Not able to fetch CI Response"
            return None


def find_between(s, first, last):
    """
    internal function used in send_xmlFile_CI
    :param s:
    :param first:
    :param last:
    :return:
    """
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""

#####################################################################################################################
def updatetimsresultsjson(cfg,start_time,end_time,results_json,testcategory):
    """
        Common function used in all scripts in doit
        :param cfg: get the lab config parameter from the script
        :param start_time: get the starttime of the script
        :param end_time: get the endtime of the script
        :param testcategory: get the testcategory in which tims results needs to update
        :return:
    """
    try:
        time_value = end_time - start_time
        time_value = round(time_value , 6 )
        time_value = str(time_value)
        filename =  cfg['test_results']['filename']
        data = {
            "config": {
                "labname" : cfg['LABNAME'] ,
                "extraconf" : str(cfg['EXTRACONF']) ,
                "gitrepo" : cfg['GITREPO'] ,
                "gitlastcommit" :  cfg['GITLASTCOMMIT'] ,
                "description" : cfg['lab-description']
               }
            }
        timsResults = JsonReadWrite(filename)
        timsResults.writeDictJson(data)
        status_value = []
        for key,val in dict.items(results_json):
            TC = key
            US = val[0]
            message = val[1]
            status_value.append(val[2])
            if val[2] == 0 or val[2] == 2:
                status = "PASS"
            elif val[2] == 3:
                status = "Not Run"
            elif val[2] == 4:
                status = "Unsupported"
            else:
                status = "FAIL"
            name  =  inspect.stack()[1][1]
            filename =  os.path.basename(name)
            name = filename[0:-3]
            # message will eventually be the last log message but this is a proof of concept
            results = {
                "CF": "",
                "I": "Core DVR Functionality",
                "MF": "",
                "TC": TC,
                "US": US,
                "message": message,
                "name": name,
                "status": status,
                "time": time_value
                }
            timsResults.appendListToKey('testsuite:'+testcategory, results)
        if status_value :
            if ( 1 in status_value ) or ( 3 in status_value) :
                return (1)
            elif (4 in status_value) or (2 in status_value):
                return (2)
            else :
                return (0)
        else :
             print "status_value not present "
             return 1
    except:
        print "Exception in Script"
        PrintException()
        return 1
##############################################################################################################################

def modifyXML(path,extensionSecs = 0, startMin = 0, endMin = 0):
    """
    Modify schedule/post  XML by giving the path.
    Used to modify endTime, or startTime, or duration of the individual event only. For Series, call modifyXML_series
    :param path:
    :param extensionSecs:
    :param startMin:
    :param endMin:
    :return:
    """
    starttime_new = 0
    endtime_new = 0

    with open(path) as xmlfile:
         lines = [line for line in xmlfile if line.strip() is not ""]

    with open(path, "w") as xmlfile:
         line1, last_line = lines[1], lines[-1]
         del lines[1], lines[-1]
         xmlfile.writelines(lines)

    line1 = line1
    last_line = '\n' + last_line
    tree = ET.parse(path)
    root = tree.getroot()
    time.sleep(5)

    if extensionSecs:
        # Adding n mins extra to the duration value
        for duration in root.findall(".//duration"):
            default_duration = int(duration.text)
            updated_duration = int(duration.text) + extensionSecs
            duration.text = str(updated_duration)
    if endMin:
        endtime_text = None
        # Adding n mins extra to endDateTime value
        for endTime in root.findall(".//InstanceAvailability/endDateTime"):
            default_min = endTime.text.split(":")
            default_min[1] = str(int(default_min[1]) + endMin)
            updated_min = default_min[1]
            if len(updated_min)!= 2:
               updated_min = updated_min.zfill(2)
               endtime_text = default_min[0] + ":" + updated_min + ":" + default_min[2]
               endTime.text = endtime_text
            elif len(updated_min) == 2 and int(updated_min) >= 60:
               extra_min = divmod(int(updated_min), 60)
               new_hour = str(int(default_min[0][-2:]) + extra_min[0])
               if len(new_hour) != 2:
                  new_hour = new_hour.zfill(2)
               if len(str(extra_min[1])) != 2:
                  extra_min[1] = str(extra_min[1]).zfill(2)
               endtime_text = default_min[:-2] + new_hour + ":" + extra_min[1] + ":" + default_min[2]
            elif len(updated_min) == 2 and int(updated_min) <= 60:
                endtime_text = default_min[0] + ":" + updated_min + ":" + default_min[2]
            endTime.text = endtime_text

    if startMin:
        #Modifying StartTime of the event
        for startTime in root.findall(".//InstanceAvailability/startDateTime"):
            default_min_start = startTime.text.split(":")
            default_min_start[1] = str(int(default_min_start[1])+ startMin)
            updated_min_start = default_min_start[1]
            if len(updated_min_start)!= 2:
               updated_min_start = updated_min_start.zfill(2)
               starttime_text = default_min_start[0] + ":" + updated_min_start + ":" + default_min_start[2]
               startTime.text = starttime_text
            elif len(updated_min_start) == 2 and int(updated_min_start) >= 60:
               extra_min_start = divmod(int(updated_min_start), 60)
               new_hour_start = str(int(default_min[0][-2:]) + extra_min_start[0])
               if len(new_hour_start) != 2:
                  new_hour_start = new_hour_start.zfill(2)
               if len(str(extra_min_start[1])) != 2:
                  extra_min_start[1] = str(extra_min_start[1]).zfill(2)
               starttime_text = default_min_start[:-2] + new_hour_start + ":" + extra_min_start[1] + ":" + default_min_start[2]
            elif len(updated_min_start) == 2 and int(updated_min_start) <= 60:
               starttime_text = default_min_start[0] + ":" + updated_min_start + ":" + default_min_start[2]
            startTime.text = starttime_text
            print starttime_text

    if startMin and endMin:
        for titleEndTime in root.findall(".//title/endDateTime"):
            titleEndTime.text = endtime_text
        for titleStartTime in root.findall(".//title/startDateTime"):
            titleStartTime.text = starttime_text

    tree.write(path)

    # Verification if the values are updated correctly
    tree = ET.parse(path)
    root = tree.getroot()
    time.sleep(5)
    result_list = []
    if extensionSecs:
        # Verification of 3 mins extra to the duration value
        for verify_duration in root.findall(".//duration"):
            retrieved_duration = int(verify_duration.text)
            print "actual duration %d updated duration %d" % (retrieved_duration,updated_duration)
            if updated_duration == retrieved_duration:
               print "Duration value is correctly updated"
            else:
               print "Duration verification failed"
               result_list.append("FAIL")
    if endMin:
        # Verification for endDateTime value
        for verify_endTime in root.findall(".//InstanceAvailability/endDateTime"):
            print "actual enTime %s updated endtime %s" % (verify_endTime.text,endtime_text)
            if verify_endTime.text == endtime_text:
               print "endtime verified"
               result_list.append("PASS")
            else:
               print "Endtime is not updated in the XML"
               result_list.append("FAIL")
    if startMin:
        # Verification for endDateTime value
        for verify_startTime in root.findall(".//InstanceAvailability/startDateTime"):
            print "actual startTime %s updated starttime %s" % (verify_startTime.text,starttime_text)
            if verify_startTime.text == starttime_text:
               print "starttime verified"
               result_list.append("PASS")
            else:
               print "starttime is not updated in the XML"
               result_list.append("FAIL")

    line0 = '\n<?xml version="1.0" encoding="UTF-8"?>\n'
    with open(path, 'rb') as fp:
         lines = fp.readlines()
         lines.insert(0,line0)
         lines.insert(1,line1)
         lines.append(last_line)
    with open(path, 'w') as fp1:
         for ele in lines:
             fp1.writelines(ele)
         fp1.close()

    if "FAIL" in result_list: return False
    else: return True
#######################################################################################################################
def send_xmlFile_CI_withURIid(xmlFile, cfg,uri_command,uri_id):
    """
    Once an XML is edited, we call this function to Post the same XML. Input the below params.
    :param xmlFile:
    :param cfg:
    :param uri_command:
    :param uri_id:
    :return:
    """

    host = cfg['ci']['host']
    port = cfg['ci']['port']
    timeout = 10
    header = {
        'Content-Type': 'application/xml',
    }
    url = 'http://' + str(host) + ':' + str(port) + '/' + str(uri_command) + '/' + str(uri_id)
    print url
    with open(xmlFile, 'r') as fptr:
        contents = fptr.read()
        contents = contents.strip()
        r = requests.put(url, headers=header, data=contents, timeout=timeout)
        print r.status_code
        print r.headers
        print r.content
        if r is not None:
            if r.status_code != 200:
                print "error in posting the xml to the CI host via  url %s" % url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                return "PASS"
        else:
            print "Not able to fetch CI Response"
            return None
#######################################################################################################################################################
def verify_series_collapse_booked(group_id_list,port,protocol,pps_host,householdid,timeout,printflg=False):
    count  = 0
    if isinstance(group_id_list,list):
        if group_id_list :
            print "group id list" , group_id_list
            for group_id in group_id_list :

                url =  protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog?collapse=true&filter:state=BOOKED&filter:state=RECORDING"
                print "series collapse for booked and recording response via url %s\n " %url
                r = sendURL ("get",url,timeout)
                print r.content
                if r is not None :
                    if r.status_code != 200:
                        print "series collaspe fetching failed via  url %s"%url
                        print r.status_code
                        print r.headers
                        print r.content
                        return ("FAIL",None)
                    else:
                        if r.content == "[]":
                            print "series collaspe Response is empty"
                            return ("FAIL",None)
                        else:
                             temp = Inner_Series_collaspe_verification(r.content,group_id)
                             if temp  == "PASS" :
                                count = count + 1
                else:
                    print "unable to fetch series collaspe response"
                    return ("FAIL",None)
            if count  == len(group_id_list):
                   print "series collapsed successfully"
                   return ("PASS",r)
            else:
                print "series does not collapse successfully"
                return ("FAIL",None)
        else:
             print "unable to fetch series collaspe response"
             return ("FAIL",None)
    else:
        print "unable to fetch series collaspe response"
        return ("FAIL",None)
#######################################################################################################################################################
def verify_series_expand_booked(group_id_list,port,protocol,pps_host,householdid,timeout,printflg=False):
    count  = 0
    if isinstance(group_id_list,list):
      if group_id_list :
        print "group id list" , group_id_list
        for group_id in group_id_list :
            url =  protocol + "://" + str(pps_host) + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog?filter:series=" + str(group_id) + "&filter:state=BOOKED&filter:state=RECORDING"
            print "series expand for booked and recording via %s\n " %url
            r = sendURL ("get",url,timeout)
            if r is not None :
                if r.status_code != 200:
                    print "series expand failed  via  url %s"%url
                    print r.status_code
                    print r.headers
                    print r.content
                    return ("FAIL",None)
                else:
                    if r.content == "[]":
                        print " Service Response is empty"
                        return ("FAIL",None)
                    else:
                         temp = Inner_Series_expand_verification(r.content,group_id)
                         if temp  == "PASS" :
                            count = count + 1
            else:
                print "Not able to fetch Grid Response"
                return ("FAIL",None)
        if count  == len(group_id_list):
                print "series expanded successfully"
                return ("PASS",r)
        else:
              print "series does not expand successfully"
              return ("FAIL",None)
      else:
         print "group id list is empty "
         return ("FAIL",None)
    else:
         print "group id list is empty "
         return ("FAIL",None)
##############################################################################################################################################
def modify_keep_event(protocol, pps_host, port_pps, timeout, urilist, keepflag = "true"):
    try:
        keep_modified = []
        if isinstance(urilist, list):
            contenturilist = urilist
        else:
            contenturilist = [urilist]
        keep_headers = {
            'Content-Type': 'text/plain'
        }
        for contenturi in contenturilist:
            url = protocol + "://"+ pps_host + ":" + str(port_pps) + str(contenturi)+ "/keep"
            r = sendURL("put", url, timeout, keep_headers, str(keepflag))
            print "Recordings to keep is modified via URL : ", url
            if r is not None :
                if r.status_code != 200:
                    print "Recordings to keep modification failed  via URL %s"%url
                    print r.status_code
                    print r.headers
                    print r.content
                    return("FAIL", "Unable to modify Keep flag for recording")
                else:
                    keep_modified.append(contenturi)
            else:
                return("FAIL", "Modify Keep flag api returns None")
        if len(keep_modified) == len(contenturilist):
            message = "Able to Set the Keep Value for the Recording"
            print message
            return("PASS", message)
        else:
            message = "Unable to modify keep for %s recording" %(str(len(contenturilist) - len(keep_modified)))
            print message
            return("FAIL", message)
    except Exception as e:
        print "Error in modify_keep_event :\n", str(e)
        return("FAIL", "Error in modify_keep_event function")
##############################################################################################################################################


def get_sm_api_token(cfg,timeout):
    """
    Generate the sm_api_token
    :param cfg:
    :return:
    """

    try:
        protocol = cfg["v2p"]["protocol"]
        v2p_host = cfg["v2p"]["masters"][0]
        v2p_port = cfg["v2p"]["mgmt_port"]

        header = {
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            'authorization': 'Basic YWRtaW46ZGVmYXVsdA =='
        }

        contents = """{
                        "username": "admin",
                        "password": "default"
                    }"""

        url = protocol+"://"+v2p_host+":"+str(v2p_port)+"/api/platform/login"
        r = requests.post(url, headers=header, data=contents, timeout=timeout, verify=False)
        assert r is not None, "Error in retriving the sm api token"
        assert r.status_code == 200, "V2P return response if not 200"
        if "token" in r.content:
            return ast.literal_eval(r.content)['token']
        else:
            print r.content
            return r.content

    except AssertionError as ae:
        print "AssertionError : ", str(ae)
        return False
    except Exception as e:
        print "Error :\n", str(e)
        return False

#######################################################################################################################################
# Function to override the global config if a local config is present under an specific node
#         1. There can be scenarios where the global username is not same for all nodes like pps, sr, etc.So there can be node 
#            specific 'username' and can be accessed as below,
#         2. If there is no local 'username' present the function will look for the global 'username' and return the config accordingly.
# Example:
#         username = cfg['pps']['username']
# Usage:
#         override_global_config_value(cfg, 'pps', 'username')
########################################################################################################################################
def override_global_config_value(cfg, parent_node, search_key):
    if search_key in cfg[parent_node].keys():
        return cfg[parent_node][search_key]
    else:
        return cfg[search_key]

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

def switch_vmr_host(cfg, vmr):
    cfg["vmr"]["host"] = vmr
