'''
This file is a common library of reusable Level2 Functions.It should  strictly contain functions performing a basic/unitary test action. 
Level 2 functions can be invoked by Level3 Functions and the main script.
'''
import time
import json
import requests
import sys
import re
import datetime
import os
from L1commonFunctions import *
import subprocess
#####################################################################################################################
def fetch_serviceIdbyregion(protocol,host,port,region,timeout):
    """
    To get the serviceId list based on the region.
    Widely used in Sanity test cases
    :param protocol:
    :param host:
    :param port:
    :param region:
    :param timeout:
    :return:
    """
    url = protocol + "://" + host + ":" + str(port) + "/cmdc/services/?region=" + str(region) + "&count=255"
    print url
    r = sendURL ("get",url,timeout)
    if r is not None :
        if r.status_code != 200:
            print "Problem accessing: " + url
            print r.status_code
            print r.headers
            print r.content
        else:
            return r

#####################################################################################################################
def get_serviceIdlist(json_response):
    """
    To get the services from grid response with cdvrAvailable is True
    :param json_response:
    :return:
    """
    cdvrServices = []
    try:
        services = json.loads(json_response.text)['services']
        for service in services:
            if service['cdvrAvailable'] == True:
                cdvrServices.append( service['id'] )
    except:
        print "Failed to get services with cdvr flag set "
    return(cdvrServices)

#######################################################################################################################
def fetch_catalogbyFilter(port,protocol,pps_host,householdid,filter_para,filter_value,timeout):
    """
    To get the catalogue based on the specific filter and vale
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param filter_para:
    :param filter_value:
    :param timeout:
    :return:
    """
    try:
        #http://211.208.160.40:6060/pps/households/{householdId}/catalog?filter:state=RECORDED
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog?filter:" + filter_para + "=" + filter_value
        print "get all events by:  %s\n " %url
        r = sendURL ("get",url,timeout)
        if r is not None :
            if r.status_code != 200:
                print "Pps Booking Failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
            else:
                return r
    except:
        PrintException()

#######################################################################################################################
def fetch_catalogbyState(port,protocol,pps_host,householdid,state_value,timeout):
    """
    To get the catalogue response based on a STATE filter, it may be booked / recording / recorded / Failed
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param state_value:
    :param timeout:
    :return:
    """
    try:
        #http://211.208.160.40:6060/pps/households/{householdId}/catalog?filter:state=RECORDED
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog?filter:state=" + state_value

        print "get all events by:  %s\n " %url
        r = sendURL ("get",url,timeout)
        if r is not None :
            if r.status_code != 200:
                print "Pps Booking Failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
            else:
                return r
    except:
        PrintException()

#######################################################################################################################
def print_failedrecording_catalog(port,protocol,pps_host,householdid,timeout):
    """
    Print the catalogue based on failed state
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :return:
    """
    try:
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog?filter:state=FAILED" 

        print "get all events by:  %s\n " %url
        r = sendURL ("get",url,timeout)
        if r is not None :
            if r.status_code != 200:
                print "Print failed recording failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
            else:
                print "failed recording catalog:\n" + json.dumps(json.loads(r.content), indent=4,sort_keys=False)
    except:
        PrintException()
#######################################################################################################################
def fetch_failedrecording_catalog(port,protocol,pps_host,householdid,timeout):
    """
    To get the catalogue response on Failed state
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :return:
    """
    try:
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog?filter:state=FAILED" 

        print "get all failed recording catalog by:  %s\n " %url
        r = sendURL ("get",url,timeout)
        if r is not None :
            if r.status_code != 200:
                print "fetch failed recording catalog failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                if r.content == "[]":
                    print "Failed Recording Catalog is empty"
                    return None
                else:
                    return r
        else:
            print "Not able to fetch the Failed Recording Catalog"
            return None
    except:
        PrintException()
#######################################################################################################################
def fetch_catalogbyContentId(port,protocol,pps_host,householdid,contentId_value,timeout):
    """
    To get the catalogue response with the Content ID filter
    Used in delete_events_from_booklist of L3commonFunction
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param contentId_value:
    :param timeout:
    :return:
    """
    try:
        #http://211.208.160.40:6060/pps/households/{householdId}/catalog?filter:state=RECORDED
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog?filter:contentId=" + contentId_value

        print "get all events by:  %s\n " %url
        r = sendURL ("get",url,timeout)
        if r is not None :
            if r.status_code != 200:
                print "Pps Booking Failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                if r.content == "[]":
                    print "Catalog is Empty"
                    return None
                else:
                    return r
        else:
            print "Not able to fetch the Catalog by Content ID"
            return None
    except:
        print "Exception Occurred in fetching Catalog"
        PrintException()
        return None

#######################################################################################################################
def fetch_bookingCatalog(port,protocol,pps_host,householdid,timeout):
    """
    To get the booking catalogue for the a particular household
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :return:
    """
    try:
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/bookings"
        print "get all Bookings by:  %s\n " %url
        r = sendURL ("get",url,timeout)
        if r is not None :
            if r.status_code != 200:
                print "Fetching Booking Catalog Failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                if r.content == "[]":
                    print "Booking Catalog is empty"
                    return None
                else:
                    return r
        else:
            print "Not able to fetch the Booking Catalog"
            return None
    except:
       print "Exception occurred in fetching Booking Catalog"
       PrintException()
       return None

#######################################################################################################################
def fetch_recordingCatalog(port,protocol,pps_host,householdid,timeout):
    """
    To get the recording catalogue for a particular household
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :return:
    """
    try:
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/recordings"
        print "get all Recordings by:  %s\n " %url
        r = sendURL ("get",url,timeout)
        if r is not None :
            if r.status_code != 200:
                print "Fetching Recording Catalog Failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                if r.content == "[]":
                    print "Recording Catalog is empty"
                    return None
                else:
                    return r
        else:
            print "Not able to fetch the Recording Catalog"
            return None
    except:
       print "Exception occurred in fetching Recording Catalog"
       PrintException()
       return None

#######################################################################################################################
def fetch_household_Catalog(port,protocol,pps_host,householdid,timeout):
    """
    To get the Catalogue items of a particular household
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :return:
    """
    try:
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog"
        print "get all Catalog by:  %s\n " %url
        r = sendURL ("get",url,timeout)
        if r is not None :
            if r.status_code != 200:
                print "Fetching Recording Catalog Failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                if r.content == "[]":
                    print "Household Catalog is empty"
                    return None
                else:
                    return r
        else:
            print "Not able to fetch the household Catalog"
            return None
    except:
       print "Exception occurred in fetching Household Catalog"
       PrintException()
       return None
#############################################################################################################################################
def fetch_Catalog(port,protocol,pps_host,householdid,timeout):
    """
    To get the Catalogue items of a particular household
    :param port:
    :param protocol:
    :param pps_host:
    :param householdid:
    :param timeout:
    :return:
    """
    try:
        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/households/" + str(householdid) + "/catalog"
        print "get all Catalog by:  %s\n " %url
        print "Current system time while fetching the catalog " + str(datetime.datetime.utcnow())
        r = sendURL ("get",url,timeout)
        if r is not None :
            if r.status_code != 200:
                print "Fetching Recording Catalog Failed via  url %s"%url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                if r.content == "[]":
                    print "Recording Catalog is empty"
                    return None
                else:
                    #print "Catalog Response\n" + json.dumps(json.loads(r.content),indent=4,sort_keys=False)
                    return r
        else:
            print "Not able to fetch the Recording Catalog"
            return None
    except:
       print "Exception occurred in fetching Recording Catalog"
       PrintException()
       return None

########################################################################################################################
def get_nodesList(protocol,host,port,timeout):
  try:
    url = protocol + "://" + host + ":" + str(port) + "/api/v1/nodes"
    print url
    r = sendURL ("get", url, timeout)
    if r is not None:
        if r.status_code !=200:
            print "Problem accessing: " + url
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            node_list = []
            responce = json.loads(r.content)
            for values in responce['items']:
                node_name = values['metadata']['name']
                node_list.append(node_name)
            return node_list
  except:
    PrintException()

########################################################################################################################
def search_data_from_keyvalue(search_data,TC_name,cwd_path):
    """
    To get the value from the keyvalue file in Longterm Verify script
    :param search_data:
    :param TC_name:
    :param cwd_path:
    :return:
    """
    verify_list = []
    for val in search_data:
        temp =  TC_name + "/" + val
        searchfile = open( cwd_path + "/keyvalues", "r")
        for line in searchfile:
            if temp in line:
               temp_line = line
               value = temp_line.split("=")[-1]
               verify_list.append(value)
        searchfile.close
    return verify_list
###########################################################################################################################
def write_data_for_EC(data,file_name,TC_name):
    """
    To write the details of the sci
    :param data: data to be written ['householdid='+ householdid,'message='+ message,'tims_flag='+ "True",'random_contentId_list='+ ','.join(random_contentId_list)]
    :param file_name:
    :param TC_name:
    :return:
    """
    for value in data:
        with open(file_name,'a+') as f:
            f.write('longterm/'+ TC_name + "/" + value + "\n" )
    f.close()
########################################################################################################################
def get_cdvr_asset(cfg):
   try :
        if cfg['v2p']['use_proxy'] is False:
           v2p_host = cfg['v2p']['assets_url']
        else:
           v2p_host = cfg['v2p']['masters'][0]
        v2p_port =  cfg['v2p']['interface_port']
        v2p_protocol =  cfg['v2p']['protocol']
        timeout = 10
        cdvr_asset = None
        url =  v2p_protocol + "://" + v2p_host + ":" + str(v2p_port) + "/v1/assetworkflows"
        r = sendURL ("get",url,timeout)
        if r is not None :
            if ( r.status_code != 200):
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                if r.content is not None:
                    status_val = json.loads(r.content)
                    status = json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                    for val in status_val:
                        cdvr_asset =  val["workflowId"]
                    return cdvr_asset
                else :
                     print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                     response = json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                     print "catalog response : \n\n"
                     print response
                     print "\n" + "#"*20 + " DEBUG ENDED "+ "#"*20+ "\n"
                     return None
        return None
   except:
        PrintException()
        return None

        
########################################################################################################################################
def get_cache_endpoint(cfg,header,cache_type_list):
   try :
        v2p_host = cfg['v2p']['masters']
        v2p_port =  cfg['v2p']['mgmt_port']
        v2p_protocol =  cfg['v2p']['protocol']
        timeout = 10
        cache_name_list = []
        url = v2p_protocol + "://" + v2p_host[0] + ":" + str(v2p_port) + "/sm/v2/type/appinstances"
        r = sendURL ("get",url,timeout,header)
        if r is not None :
            if ( r.status_code != 200):
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                if r.content is None :
                    print "\n" + "#"*20 + " DEBUG STARTED "+ "#"*20+ "\n"
                    printLog("Get cache endpoint :  \n" + r.content,printflg)
                    print "\n" + "#"*20 + " DEBUG ENDED   "+ "#"*20+ "\n"
                    return None
                status_val = json.loads(r.content)
                status = json.dumps(json.loads(r.content),indent = 4, sort_keys=False)
                for cache_type in cache_type_list:
                    try:
                        for val in status_val:
                            if val["properties"]["type"] == cache_type:
                                cache_name = val["name"]
                                print cache_name
                                cache_name_list.append(cache_name)
                    except:
                           pass
                return cache_name_list
        return None
   except:
        PrintException()
        return None

########################################################################################################################################
def get_workflowname_list(v2p_protocol,v2pmasternode,port,headers,asset_type,timeout):
    workflowname_list = []
    try:
        url = v2p_protocol + "://" + v2pmasternode + ":" + str(port) + "/v2/regions/region-0/serviceapis"
        print "Get  service api via " + url
        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                print "could not Get service api for v2p master node: " + v2pmasternode
                print r.status_code
                print r.headers
                print r.content
            else:
                print "\Get service api = " + r.content
                print "Got the service api succesfully for v2pnode: " + v2pmasternode
                responce = json.loads(r.content)
                for value in responce:
                    try:
                        interface_list = value['properties']['interfaces']
                        for interface in interface_list :
                             workflowname = interface['assetWorkflowTemplate']
                             workflowname_list.append(workflowname)
                    except:
                        PrintException()
        if workflowname_list:
            print "Workflow name list: " , workflowname_list
            workflowname_list = [x for x in workflowname_list if re.search(asset_type, x)]
            return workflowname_list
        else:
            return None
    except:
        PrintException()
        return None
###################################################################################################################################
def get_service_list(cfg):
    """
    To get the service id list from the CMDC response
    :param cfg:
    :return:
    """
    try :
        protocol = cfg['protocol']
        host = cfg['cmdc']['host']
        port = cfg['cmdc']['port']
        region = cfg['region']
        headers = {
            'Accept': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }
        timeout = 5
        service_list = []
        url = protocol + "://" + host + ":" + str(port) + "/cmdc/services?region=" + str(region) + "&count=255"
        print "CMDC Service details fetched via %s"%url
        r = sendURL ("get",url,timeout,headers)
        if r is not None :
            if ( r.status_code != 200):
                print "Problem accessing: " + url
                print r.status_code
                print r.headers
                print r.content
                return None
            else:
                 services = json.loads(r.text)['services']
                 for service in services:
                     channel = service['id']
                     service_list.append(channel)
                 return service_list
        return None
    except:
        PrintException()
        return None
############################################################################################################################################

def get_content_playbackURI(pps_host, pps_port, protocol, contentid_list, householdid_list, timeout):
    """
    To get the list of contentplayURI for a list of contentIds and list of household ID.
    :param pps_host:
    :param pps_port:
    :param protocol:
    :param contentid_list:
    :param householdid_list:
    :param timeout:
    :return:
    """
    try:
        contentplaybackURI_list = []
        household_counter = 0
        if not isinstance(householdid_list, list):
            householdid_list = [householdid_list]
        for householdid in householdid_list:
            jsonrecordingcatalog = fetch_recordingCatalog(pps_port, protocol, pps_host, householdid, timeout)
            if jsonrecordingcatalog is not None:
                jsonrecordedcontent = json.loads(jsonrecordingcatalog.content)
                contentplayback_counter = 0
                for contentid in contentid_list:
                    for cont in jsonrecordedcontent:
                        if cont["household"] == householdid:
                            if contentid == cont["scheduleInstance"]:
                                contentplayuri = cont['contentPlayUri']
                                contentplaybackURI_list.append(contentplayuri)
                                contentplayback_counter += 1

                if contentplayback_counter == len(contentid_list):
                    household_counter = household_counter + 1
                else:
                    print "Length of ContentPlaybackURI list is not equal to the content id list :", contentplaybackURI_list
                    return None
            else:
                print "Recording catalogu response is None for household:", householdid
                return None

        if household_counter == len(householdid_list):
            return contentplaybackURI_list
        else:
            print "Length of Household counter list is not equal to household id list: ", contentplaybackURI_list
            return None

    except Exception as e:
        print "Exception in get_content_playbackURI :", str(e)
        return None

#####################################################################################################################
def get_recId_from_contentplaybackURI(playbackurilist):
    """
    To get the content Recording Id list from the contnentplayURI
    :param playbackurilist:
    :return:
    """
    try:
        recidlist = []
        for playbackuri in playbackurilist:
            id = re.search('recId=(.+?)&type', playbackuri)
            if id:
                recId = id.group(1)
                recidlist.append(recId)
            else:
                print "ContentPlayBackURI does not have recId"
        if len(playbackurilist) == len(recidlist):
            return recidlist
        else:
            print "Lenght of recid list is not equal to contentplaybackuri list :",recidlist
            return None
    except Exception as e:
        print "Exception in get_recId_from_contentplaybackURI :", str(e)
        return None
#####################################################################################################################

def get_contentid_from_recid(cfg, playbackurilist,timeout):
    """
    To get the content id list from recording Id using the RM response
    """
    try:
        recid_list = get_recId_from_contentplaybackURI(playbackurilist)
        if recid_list:
            protocol = cfg['protocol']
            rm_host = cfg['rm']['host']
            headers = {
                        'content-type': 'application/json',
                        'Accept': 'application/json'
                       }
            contentid_list = []
            for recId in recid_list:
                url = protocol+"://"+rm_host+"/recordingInfo/"+recId+"?contentType=MPEG4&mode=playback&responseFormat=json"
                print "URL to get contentid from recoring id :",url
                r = sendURL ("get", url, timeout, headers)
                if r is not None:
                    if r.status_code != 200:
                        print "Unable to get the contentIds with URL :",url
                        print r.status_code
                        print r.headers
                        print r.content
                        return None
                    else:
                        #print "Contentid from Recid response:",r.content
                        jsonresponse = json.loads(r.content)
                        contentId = jsonresponse['playlist']['segment'][0]["contentId"]
                        contentid_list.append(contentId)
                else:
                    return None
            if len(contentid_list) == len(recid_list):
                return contentid_list
            else:
                print "Length of content id list is not equal to the recording id list :",contentid_list
                return None
        else:
            return None
    except Exception as e:
        print "Exception in get_ContentId_from_recId :", str(e)
        return None
#####################################################################################################################

def get_start_and_end_time(cfg, contentidlist, timeout):
    """
    To get the start time and the end time of the contentId from the VMR response
    :param cfg:
    :param contentidlist:
    :param timeout:
    :return: List of ActualStarttime, ActualEndtim, StreamID, ISID, BatchID
    """
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
        streamid_start_end_time_list = []
        startendtime_counter = 0

        for contentid in contentidlist:
            templist = []
            url = protocol + "://" + vmr_host + ":" + str(vmr_port) + "/api/findxrid/" + contentid
            print "\nURL to get the stream id, start time and end time:", url
            r = sendURL("get", url, timeout, headers)
            # print "VMR response :",r.content
            if r is not None:
                if r.status_code != 200:
                    print "Unable to get the start and end time with URL :", url
                    print r.status_code
                    print r.headers
                    print r.content
                    return None
                else:
                    jsonresponse = json.loads(r.content)
                    print "JSON response :", r.content
                    for item in jsonresponse:
                        starttime = item["ActualStartTime"]
                        endtime = item["ActualEndTime"]
                        streamId = item["StationID"]
                        isid = item["ISID"]
                        batchid = item["BatchID"]

                    if starttime and endtime and streamId and isid and batchid :
                        templist.append(streamId)
                        templist.append(starttime.replace(':', "").replace("-", "").replace("T", "").replace("Z", ""))
                        templist.append(endtime.replace(':', "").replace("-", "").replace("T", "").replace("Z", ""))
                        templist.append(isid)
                        templist.append(batchid)
                        streamid_start_end_time_list.append(templist)
                        startendtime_counter += 1
                    else:
                        print "Unable to get the start and end time from the JSON response for content id: ", str(contentid)
                        return None
            else:
                print "Not able to fetch Grid Response"
                return None
                # Verify the start and end time
        if len(contentidlist) == startendtime_counter:
            return streamid_start_end_time_list
        else:
            print "Final StremId, Strart time and End Time list :", streamid_start_end_time_list
            return None

    except Exception as e:
        print "Exception in get_start_and_end_time :", str(e)
        return None


######################################################################################################################


def compare_time_list(time_list):
    """
    To compare the elements in the list and return the list of list of unique value.
    :param time_list:
    :return:
    """
    final_list = []
    try:
        if len(time_list) > 1:
            temp = set([x for x in time_list if time_list.count(x) > 1])
            for vl in temp:
                temp_list = []
                for vl1 in time_list:
                    if vl == vl1:
                        temp_list.append(vl1)
                final_list.append(temp_list)
            return final_list
        else:
            return [time_list]
    except Exception as e:
        print "Exception in compare_time_list :",str(e)
        return None
#######################################################################################################################
def get_segment_response(cfg, startendtime, streamid, timeout):
    """
    To get the segment response in a time window based on the streamid from VMR reponse
    :param cfg:
    :param startendtime:
    :param streamid:
    :param timeout:
    :return:
    """
    try:

        startTime = str(startendtime[0]).split('.')[0]
        endTime = str(startendtime[1]).split('.')[0]

        protocol = cfg['protocol']
        vmr_host = cfg['vmr']['host']
        vmr_port = cfg['vmr']['port']
        url = protocol+"://"+str(vmr_host)+":"+str(vmr_port)+"/api/streams/"+str(streamid)+"/segments?start="+startTime+"&end="+endTime
        print "URL to get segment response :",url
        r = sendURL("get", url, timeout)
        if r is None:
            return None
        if r.status_code != 200:
            print "Unable to get the segment response with URL :",url
            print r.status_code
            print r.headers
            print r.content
            return None
        else:
            segidlist = get_segmentId_list(r)
            return segidlist
    except Exception as e:
        print "Exception in get_segment_response :", str(e)
        return None

####################################################################################################################


def get_segmentId_list(segmentresponse):
    """
    To get the list of segment Ids from the segment response
    :param segmentresponse:
    :return:
    """
    try:
        segmentIdList=[]
        res = json.loads(segmentresponse.content)
        for itm in res:
            segmentIdList.append(itm['SegmentID'])
        return segmentIdList
    except Exception as e:
        print "Exception in get_segmentId_list :", str(e)
        return None

####################################################################################################################
def verify_FanOut_value(cfg, segmentIdList, isid, timeout, batchid=1,maxfanout=0,common_copy=True):
    """
    Verify all the Fanout value of the segment id list.
    If the Max fanout is 2, then verify the response from the cos for every segment id has fanout value is 0,1,2
    :param cfg: Configuration variable
    :param segmentIdList: List of segment ids
    :param streamid: stream id / channel id
    :param timeout: timeout value
    :param maxfanout: Maximum fanout value <No of housedholds>
    :return: True if all the segment ids are having the all the fanout value else False
    """

    try:
        protocol = cfg['protocol']
        cosIP = cfg['cos']['urls'][0]
        cosEnv = "rio/active"
        # cosEnv = cfg['cos']['env']

        numberOfItr = 0
        if common_copy or maxfanout == 0:
            maxfanout = 1
        for fan in range(0, maxfanout):
            response_success_list = []
            response_failue_dict = {}
            headers = {
                'X-Fanout-Copy-Index': str(fan),
                'content-type': 'application/json',
                'Accept': 'application/json',
                'Source-Type': 'SMS',
                'Source-Id': '123'
            }

            fanout_segment_list = 0

            for segmentId in segmentIdList:
                url = cosIP + "/" + cosEnv + "/isid/" + str(isid) + "/segmentid/" + str(segmentId) + "/batchid/" + str(batchid)
                #print "URL to verify fanout value:", url
                r = sendURL("get", url, timeout, headers)
                if r is not None:
                    if r.status_code != 200:
                        if r.status_code in response_failue_dict.keys():
                            response_failue_dict[r.status_code].append(segmentId)
                        else:
                            response_failue_dict[r.status_code] = [segmentId]
                    else:
                        # print "Response:",r.content
                        response_success_list.append(segmentId)
                        fanout_segment_list += 1
                else:
                    print "Response to verify fanout value is none"
                    return False

            if fanout_segment_list == len(segmentIdList):
                print "All Segment passed for fanout : ", str(fan)
                numberOfItr += 1
            else:
                print "All Segment doesn't pass for fanout : ", str(fan)
                for k,v in response_failue_dict.items():
                    print "Return code :",k," for segment ids :",v
                return None

            if common_copy: # If the content is common copy, verify the response is 416 for fanout value 1
                temp_common_copy_count =0
                cc_response_failue_dict={}
                cc_response_success_list=[]
                cc_fanout_segment_list =0

                headers = {
                    'X-Fanout-Copy-Index': '1',
                    'content-type': 'application/json',
                    'Accept': 'application/json',
                    'Source-Type': 'SMS',
                    'Source-Id': '123'
                }
                for segmentId in segmentIdList:
                    url = cosIP + "/" + cosEnv + "/isid/" + str(isid) + "/segmentid/" + str(segmentId) + "/batchid/" + str(batchid)
                    # print "URL to verify fanout value:", url
                    r = sendURL("get", url, timeout, headers)
                    if r is not None:
                        if r.status_code != 416:
                            if r.status_code in cc_response_failue_dict.keys():
                                cc_response_failue_dict[r.status_code].append(segmentId)
                            else:
                                cc_response_failue_dict[r.status_code] = [segmentId]
                        else:
                            # print "Response:",r.content
                            cc_response_success_list.append(segmentId)
                            cc_fanout_segment_list += 1

                if cc_fanout_segment_list == len(segmentIdList):
                    print "All Segment returned 416 for fanout 1 "
                    return True
                else:
                    print "Some segments does not return 416 for the fanout value 1 :",cc_response_failue_dict
                    return False

        if numberOfItr == maxfanout:
            print "Fan out value of the all the segments are verified"
            return True
        else:
            print "FanOut value of all the segment IDs are not as expected"
            return False
    except Exception as e:
        print "Exception in verify_FanOut_value :", str(e)
        return None
#####################################################################################################################

