#!/usr/bin/python

import os
import sys
import json
from pprint import pprint
import time
import requests
import calendar
import itertools
import datetime
import mypaths
import random
from os.path import isfile
from genChannelLineup import *
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
##############################################################################################################################################
# TC878:Expand and collapse epiodes within series in library
# STEP1: Ingest two series with same broadcasttime (3 Episodes of 2 minutes duration) 
# STEP2: Do the Series booking for the first Seriesi(Place holder series )
# STEP3: Series booking for the Second Series
# STEP4: Verify all the episodes of the series is present in the booked library 
# STEP5: Wait till  all the episodes get recorded and verify that all episodes are in the recorded library
# STEP6: Perform the Series collapse
# STEP7: Perform Series Expand
# STEP8: Do the Playback of any of the episodes in the series
##################################################################################################################################################################################################### 
def doit(cfg,printflg=True):
    try :
        start_time = time.time()
        rc = doit_wrapper(cfg,printflg)
        end_time = time.time()
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
        for key,val in dict.items(rc):
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
            name  =  os.path.basename(__file__)[:-3]
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
            timsResults.appendListToKey('testsuite:basic_feature', results)
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
          print  "Error Occurred in TIMS log \n"
          PrintException()
          return (1)

def doit_wrapper(cfg,printflg=False):
    message = ""
    status = 3
    tims_dict = {
        "TC878": ["US31863", message, status]
    }
    print tims_dict
    print "TC878: Expand and collapse epiodes within series in library"
    print "US31863: As a viewer, when I browse my cDVR series recordings I want to be able to expand and collapse the list of episodes within each series."
    try:
        print "### STEP1: Ingest two series with same broadcasttime (3 Episodes of 2 minutes duration) ########\n \n \n"
        title1 = 'Series' + str(random.randint(1,499))
        seriestitle = 'Series' + str(random.randint(500,999))
        episode_post_time = time.time() + 200
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ci_ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ci_ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        testchannel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        channel1 = ChannelLineup(BoundaryInMinutes=1)
        channel1.add_to_lineup(serviceId=testchannel1,timeSlotLengthMinutes=5,showID=title1,episodeCount=2,startEpisodeNumber=1,timeSlotCount=2)
        channel1.add_to_lineup(serviceId=testchannel2,timeSlotLengthMinutes=5,showID=seriestitle,episodeCount=2,startEpisodeNumber=1,timeSlotCount=2)
        End_broadcast_time =channel1.postXmlData(ci_host,ci_port,startTime =episode_post_time)
        length =channel1.getTotalLength() 
        total_ci_ingest_delay = ci_ingest_minimum_delay + length * ci_ingest_delay_factor_per_minute
        channel1.writeXmlFiles(startTime = episode_post_time)
        time.sleep(total_ci_ingest_delay)
        time.sleep(30)
        print channel1
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
        #Initialize the Variables
        timeout = 10
        serviceIdlist = []
        random_contentId = None
        randomcontentidlist = []
        recIdlist =[]
        gridservicelistresponse =None
        jsonbookedcatalog =None
        recorded_lib =None
        series_grid_episodes =None 
        # set values based on config
        upm_host = cfg['upm']['host']
        pps_hosts = [cfg['pps']['host']]
        cmdc_hosts = [cfg['cmdc']['host']]
        households_needed = cfg['basic_feature']['households_needed']
        cmdc_port = cfg['cmdc']['port']
        pps_port = cfg['pps']['port']
        catalogueId = cfg['catalogueId']
        protocol = cfg['protocol']
        region = cfg['region']
        testchannel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceIdlist.append(unicode(testchannel1))
        testchannel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        serviceIdlist.append(unicode(testchannel2))
        prefix = cfg['basic_feature']['household_prefix']
        throttle_milliseconds = cfg['basic_feature']['throttle_milliseconds']
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']
        series_bookingstatecheck = cfg['pps']['series_bookingstatecheck_waittime']
        cmdc_headers = {
            'Accept': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
                    }
        pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
                   }
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        hostlist = list(itertools.product(cmdc_hosts,pps_hosts))
        result = "Fail"
        for (cmdc_host,pps_host) in hostlist :
            cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
            gridservicelistresponse = fetch_gridRequest(catalogueId,protocol,cmdc_host,cmdc_port,serviceIdlist,region,timeout,printflg)
            if gridservicelistresponse :
                print "### STEP2: Do the Series booking for the first Seriesi(Place holder series ) ######### \n \n \n"
                time.sleep(30)
                book1_result,book1_msg,book1_contId_idlist =Series_book(pps_port,protocol,pps_host,householdid,pps_headers,timeout,title1,gridservicelistresponse,printflg)    
            else:
                message = "Grid response is empty"
                print message
                #cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                tims_dict = update_tims_data(tims_dict,1, message, ["TC878"])
                return tims_dict
            time.sleep(30)
            time.sleep(30)
            if book1_result == "PASS":
                print "### STEP3: Series booking for the Second Series ######### \n \n \n"
                book_result,book_msg,book_contId_idlist =Series_book(pps_port,protocol,pps_host,householdid,pps_headers,timeout,seriestitle,gridservicelistresponse,printflg)    
            else:
                message = book1_msg + ",Testcase Failed"
                print message
                #cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                tims_dict = update_tims_data(tims_dict,1, message, ["TC878"])
                return tims_dict
                
            time.sleep(30)
            if book_result == "PASS": 
                time.sleep(series_bookingstatecheck)
                print "###  STEP4: Verify all the episodes of the series is present in the booked library ##### \n \n \n"
                booked_result,booked_msg,booked_grp_idlist = check_bookedlib_for_allepisodes_booked(pps_port,protocol,pps_host,householdid,timeout,seriestitle,book_contId_idlist)      
            else:
                message = book_msg + ",Testcase Failed"
                print message
                #cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                tims_dict = update_tims_data(tims_dict,1, message, ["TC878"])
                return tims_dict
            time.sleep(120)
            if  booked_result == "PASS":
                length = length * 60
                print "### STEP5: Wait till  all the episodes get recorded and verify that all episodes are in the recorded library############ \n \n \n" 
                print "System will wait for  %s seconds to compleete the recording"%length
                time.sleep(length)
                time.sleep(recordedstatecheck_waittime)
                rec_result,rec_msg,contentplayuri = check_reclib_episode_booked(cfg,protocol,pps_host,pps_port,householdid,timeout,seriestitle,book_contId_idlist,printflg=False)
            else:
                message = booked_msg + ",Testcase Failed"
                print message
                #cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                tims_dict = update_tims_data(tims_dict,1, message, ["TC878"])
                return tims_dict
            if rec_result == "PASS":
                 booked_grp_idlist = dict.fromkeys(booked_grp_idlist).keys()
                 print "###  STEP6: Perform the Series collapse ############ \n \n \n"
                 collapseresult,collapseresp = Verify_Series_Collapse(booked_grp_idlist,pps_port,protocol,pps_host,householdid,timeout,printflg=False) 
            else:
                message = rec_msg + ",Testcase Failed"
                print message
                #cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                tims_dict = update_tims_data(tims_dict,1, message, ["TC878"])
                return tims_dict
            if collapseresult == "PASS":
                print "### STEP7: Perform Series Expand ############ \n \n \n"
                expandresult,expandresp = Verify_Series_expand(booked_grp_idlist,pps_port,protocol,pps_host,householdid,timeout,printflg=False)
            else:
                message = "Expand Failed, Testcase failed"
                print message
                #cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                tims_dict = update_tims_data(tims_dict,1, message, ["TC878"])
                return tims_dict
            if expandresult == "PASS":
                expandresp = json.loads(expandresp.content)
                for val in expandresp :
                    playback_title = val['title']
                    playback_uri =val['contentPlayUri']
                    print "### STEP8: Do the Playback of any of the episodes in the series ########## \n \n \n"
                    playbk_rslt,playbk_msg = playback(cfg,test,abspath,pps_port,protocol,pps_host,playback_title,playback_uri,householdid,pps_headers,timeout,printflg)          
            else:
                message = "Expand Failed, Testcase failed"
                print message
                #cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                tims_dict = update_tims_data(tims_dict,1, message, ["TC878"])
                return tims_dict
 
            if playbk_rslt == "PASS": 
                message = playbk_msg +  ", Testcase Passed"
                #cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                tims_dict = update_tims_data(tims_dict,0, message, ["TC878"])
                return tims_dict
            else:
                message = playbk_msg + ", Testcase failed"
                print message
                #cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                tims_dict = update_tims_data(tims_dict,1, message, ["TC878"])
                return tims_dict
    except:
        message = "Error occured in Script" + PrintException(True)
        print message
        cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
        tims_dict = update_tims_data(tims_dict,1, message, ["TC878"])
        return tims_dict

def Series_book(pps_port,protocol,pps_host,householdid,pps_headers,timeout,title,gridservicelistresponse,printflg):
    message =None
    contentId_list =None
    try:
        if gridservicelistresponse:
            contentId_dict_all = get_series_contentIddict_bytitle(gridservicelistresponse,title,['title','seriesId','episodeNumber'])
            if contentId_dict_all :
                contentId_list = contentId_dict_all.keys()
                series_contentId_list = sorted(contentId_dict_all.items(), key=lambda x:x[1])
                print series_contentId_list
                if len(series_contentId_list) >=2:
                    series_contentId = series_contentId_list[0][0]
                    seriesId = series_contentId_list[0][1][3]
                    series_payload = """
                          {
                           "scheduleInstanceId" : "%s",
                           "checkConflicts" : true, 
                           "pvr":"nPVR",
                           "recurrence":"SERIES"
                           } 
                           """ % (series_contentId)
                    series_result = do_PPSbooking(pps_port,protocol,pps_host,householdid,pps_headers,series_payload,series_contentId,timeout,printflg)
                    if series_result == "PASS":
                        message = "Series Booking Successfull for series %s "%seriesId
                        print message
                        return("PASS",message,contentId_list)
                    else:
                        message = "Series Booking Failed"
                        print message
                        return("FAIL",message,contentId_list)
                else:
                    message ="Episodes are missing from the Grid Response,Cannot Proceed with the testcase"
                    print message
                    return ("FAIL",message,contentId_list)
            else:
                message ="ContentId dictionary is Empty"
                print message
                return("FAIL",message,contentId_list)
        else:
            message = "Error in retrieving Grid Response"
            print  message
            return ("FAIL",message,contentId_list)
    except:
        message ="Error Occurred in Script" + PrintException(True)
        return ("FAIL",message,contentId_list)

def check_bookedlib_for_allepisodes_booked(pps_port,protocol,pps_host,householdid,timeout,title,contentId_list_of_pgms):
    jsonbookedcatalog = None
    booked_contentId_list_of_pgms =[]
    group_idlist = []
    time.sleep(60)
    try :
        jsonbookedcatalog = fetch_bookingCatalog(pps_port,protocol,pps_host,householdid,timeout)
        if jsonbookedcatalog:
            event_state = json.loads(jsonbookedcatalog.content)
            if event_state:
                if isinstance(event_state,list):
                    for val in event_state:
                        for cont_Id in contentId_list_of_pgms :
                            try:
                                if  title in val['title']:
                                    if val['scheduleInstance'] == cont_Id :
                                        booked_contentId_list_of_pgms.append(val['scheduleInstance'])
                                        if val['showId']:
                                            showId = val['showId']
                                            group_idlist.append(showId)
                            except:
                                pass  
                    print "Content Ids from the booked library" ,booked_contentId_list_of_pgms
                    print "Content Ids from the grid response" ,contentId_list_of_pgms
                    booked_contentId_list_of_pgms = sorted(booked_contentId_list_of_pgms)
                    contentId_list_of_pgms = sorted(contentId_list_of_pgms)
                    if cmp(booked_contentId_list_of_pgms,contentId_list_of_pgms) == 0:
                        message = "all booked programes are present in the booked library"
                        print message
                        return("PASS",message,group_idlist)
                    else:
                        message = "All booked programes are not present in the booked catalog"
                        print message
                        return("FAIL",message,group_idlist)
            else:
                message = " Error in fetching the booked catalog"
                print message
                return("FAIL",message,group_idlist)
        else:
            message = "Booked catalog is empty"
            print message
            return("FAIL",message,booked_group_idlist)
    except:
        message ="Error Occurred in Script" + PrintException(True)
        return ("FAIL",message,booked_group_idlist)
def check_reclib_episode_booked(cfg,protocol,pps_host,pps_port,householdid,timeout,title,contentId_list_of_pgms,printflg=False):
    recorded_lib_json = None
    recorded_contId_list = []
    contentplayuri = None
    time.sleep(60)
    try:
        recorded_lib_json =fetch_recorded_library(cfg,protocol,pps_host,pps_port,householdid,timeout,printflg=False)
        if recorded_lib_json:
            recorded_lib=json.loads(recorded_lib_json.content)
            if isinstance(recorded_lib,list):
                for val in recorded_lib:
                    try:
                        for cont_Id in contentId_list_of_pgms:
                            if cont_Id == val['scheduleInstance'] and val['state'] == "RECORDED":
                                contentplayuri = val['contentPlayUri']
                                recorded_contId_list.append(val['scheduleInstance'])
                    except:
                        pass
                print recorded_contId_list
                recorded_contId_list = sorted(recorded_contId_list)
                contentId_list_of_pgms = sorted(contentId_list_of_pgms)
                if cmp(recorded_contId_list,contentId_list_of_pgms) == 0:
                    message = "all programs are present in the recorded library"
                    print message
                    return("PASS",message,contentplayuri)
                else:
                    message = "Programs are not present in the recorded library"
                    print message
                    return("FAIL",message,contentplayuri)
        else:
            message = "Recorded library is empty "
            print message
            return("FAIL",message,contentplayuri) 
    except:
        message ="Error Occurred in Script" + PrintException(True)
        return ("FAIL",message,contentplayuri)
def playback(cfg,test,abspath,pps_port,protocol,pps_host,recordedtitle,contentplayuri,householdid,pps_headers,timeout,printflg):
    prmsupportedflag = cfg['prm_supported']
    proxyhostcheckflag = cfg['proxyHostNeeded']
    proxy_host = cfg['proxyhost']['host']
    proxy_port = cfg['proxyhost']['port']
    contentplayback_host = cfg['contentplayback']['host']
    contentplayback_port = cfg['contentplayback']['port']
    contentplayback_url = cfg['contentplayback']['url']
    rm_host = cfg['rm']['host']
    sm_port = cfg['sm']['port']
    #Playback of the recorded library
    if recordedtitle and contentplayuri:
        try:
            #Add the recorded title with _ for the Manifest and Video Sample file names
            recordedtitlesplit = recordedtitle.split(" ")
            recordedtitlejoin = '_'.join(recordedtitlesplit)
            smsessionid = None

            #Use the SM Session Method for the playback
            if prmsupportedflag == True:
                sm_host = cfg['sm']['host']
                #Set the Variables for Playback of Recorded file
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
                    message = "Error in fetching contentplayback url"
                    print message
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
                    message = "Error in fetching ContentID"
                    print message
                    return ("FAIL",message) 

            #Download the manifest file for that response
            if contentURL:
                print "Download the manifest file via" + contentURL
                manifestfileresponse = sendURL('get',contentURL,timeout,pps_headers)
                if manifestfileresponse is not None:
                    if manifestfileresponse.status_code == 200:
                        if manifestfileresponse.content == "":
                            message = "Manifestfile Response is empty"
                            cleanup_householdid_items(pps_port,protocol,pps_host,householdid,pps_headers,timeout)
                            print message
                            return ("FAIL",message) 
                        else:
                            manifestfile = test + "_" + recordedtitlejoin + "_manifest_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt"
                            with open(manifestfile,'wb') as file1:
                                file1.write(manifestfileresponse.content)
                                file1.close()

                            #Download the video Sample and Verify
                            print "Manifest for the Recorded Content\n" +manifestfileresponse.content
                            manifestfilelocation = os.getcwd() + "/" + manifestfile
                            print "Manifest file for the recorded video saved to "+ manifestfilelocation
                            videoplaybackurl = get_videoplaybackurl(manifestfilelocation,contentURL)
                            print "Download the Video Sample via" + videoplaybackurl
                            downloadfileresponse = sendURL('get',videoplaybackurl,timeout,pps_headers)
                            if downloadfileresponse is not None:
                                if downloadfileresponse.status_code == 200:
                                    if downloadfileresponse.content == "":
                                        message = "Download file response is empty"
                                        print message
                                        return ("FAIL",message) 
                                    else:
                                        downloadfile = test + "_" + recordedtitlejoin + "_file__" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".ts"
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
                                else:
                                    message = "Error in fetching downloadfileresponse contents"
                                    print message
                                    print downloadfileresponse.status_code
                                    print downloadfileresponse.content
                                    return ("FAIL",message) 
                            else:
                                message = "Error in fetching downloadfileresponse"
                                print message
                                return ("FAIL",message) 
                    else:
                        message = "Error in feching Manifest File contents"
                        print message
                        print manifestfileresponse.status_code
                        print manifestfileresponse.content
                        return ("FAIL",message) 
                else:
                    message = "Error in fetching Manifest file"
                    print message
                    return ("FAIL",message) 
            else:
                message = "Error in fetching ContentURL"
                print message
                return ("FAIL",message) 

            #Teardown the SM Session
            if prmsupportedflag == True and smsessionid != None and statinfo.st_size:
                sm_host = cfg['sm']['host']
                if teardownsmsession(protocol,sm_host,sm_port,smsessionid,printflg):
                    message = "SM Session deleted successfully and cleaned up successfully"
                    print message
                    return ("PASS",message) 
                else:
                    message = "Error in deleting SM Session"
                    print message
                    return ("FAIL",message) 
            elif prmsupportedflag == False and statinfo.st_size:
                message = "Test case passed and cleanedup successfully"
                print message
                return ("PASS",message) 
            else:
                message = "Problem in getting the sessionid or size of the video file"
                print message
                return ("FAIL",message) 
        except:
            message = "Error Occurred in Playback Session: " + PrintException(True)
            print message
            return ("FAIL",message) 
    else:
        message = "Event is not recorded successfully to continue with the playback"
        print message
        return ("FAIL",message) 



if __name__ == '__main__':
    scriptName = os.path.basename(__file__)
    #read config file 
    sa = sys.argv
    cfg = relative_config_file(sa,scriptName)
    if cfg['basic_feature']['print_cfg']:
         print "\nThe following configuration is being used:\n"
         pprint(cfg)
         print
    L = doit_wrapper(cfg, True)
    status_value = []
    for key,val in dict.items(L):
        status_value.append(val[2])
    if status_value :
        if ( 1 in status_value ) or ( 3 in status_value) :
             exit (1)
        else:
             exit(0)
    else :
          exit(1)



