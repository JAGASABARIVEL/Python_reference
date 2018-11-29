#!/usr/bin/python

import os
import sys
import json
from pprint import pprint
import time
import requests
import calendar
import itertools
import mypaths
import random
import re
from readYamlConfig import readYAMLConfigs
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from jsonReadWrite import JsonReadWrite
from genChannelLineup import *


#######################################################################################
# Virtual disk space full popup
# Fail booking request if disk quota full
#TEST STEPS:
#STEP1.Ingest the Event of 3 Minutes without the PostTime
#STEP2.Do the PPS Booking for the Household and Wait till the recording completes. Verify the Event is recorded successfully
#STEP3.Get the Enabled Services for the same Household and disable all CDVR related services
#STEP4.Verify the event is still there in the recorded library
#STEP5.Try to Playback the recorded content and verify it should not allow to play since CDVR is disabled
#STEP6.Enable back all the CDVR services 
#STEP7.Verify playback the recorded event and see it is successfully done since CDVR services are enabled back

#######################################################################################
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
            timsResults.appendListToKey('testsuite:basic-feature', results)
        if status_value :
            if ( 1 in status_value ) or ( 3 in status_value) :
                return (1)
            elif (4 in status_value) or (2 in status_value):
                return (2)
            else :
                return (0)
        else :
             print "status_value not present,Error in return code "
             return 1
    except:
          print  "Error Occurred in TIMS log \n"
          PrintException()
          return (1)

def doit_wrapper(cfg,printflg=False):
    try :
        message = ""
        status = 3
        tims_dict = {
                 "TC1645":["US31202",message,status],
                }
        print "\nUS31202: Suspend a household"
        print "\nTC1645:Re-authorize a household for Cloud DVR, ensure household can playout existing recordings"
        # announce
        abspath = os.path.abspath(__file__)
        scriptName = os.path.basename(__file__)
        (test, ext) = os.path.splitext(scriptName)
        print "Starting test " + test
        tims_log = []
        #Initialize the Variables
        serviceidlist =[]
        timeout = 30
        full_diskquota = None
        full_diskquota1 = None
        booking_catalog = None
        recordedcontentresponse = None
        grid_response = None
        # set values based on config
        protocol = cfg['protocol']
        port_upm = cfg['upm']['port']
        port_pps = cfg['pps']['port']
        port_cmdc = cfg['cmdc']['port']
        region = cfg['region']
        catalogueId = cfg['catalogueId']
        channel1 = cfg['test_channels']['GenericCh1']['ServiceId']
        serviceidlist.append(unicode(channel1))
        channel2 = cfg['test_channels']['GenericCh2']['ServiceId']
        serviceidlist.append(unicode(channel2))
        upm_hosts =  [cfg['upm']['host']]
        recordingstatecheck_waittime = cfg['pps']['booked_to_recording_delay']
        recordedstatecheck_waittime = cfg['pps']['recording_to_recorded_delay']   
        prefix = cfg['basic_feature']['household_prefix']
        print "### STEP1 Ingest the Event of 3 Minutes without the PostTime#################################### \n \n "
        eventtitle = 'Event' + str(random.randint(100,199))
        post_time = time.time()+120
        ci_host =cfg['ci']['host']
        ci_port = cfg['ci']['port']
        ingest_minimum_delay = cfg['ci']['ingest_minimum_delay']
        ingest_delay_factor_per_minute = cfg['ci']['ingest_delay_factor_per_minute']
        channel = ChannelLineup(BoundaryInMinutes=0)
        channel.add_to_lineup(serviceId=channel1,timeSlotLengthMinutes=4,timeSlotCount=2,programIDPrefix = eventtitle)
        ingest_endtime = channel.postXmlData(ci_host,ci_port,startTime = post_time)
        channel.writeXmlFiles(startTime = post_time)
        print channel
        length = channel.getTotalLength()
        sleep_channel = ingest_minimum_delay + length * ingest_delay_factor_per_minute
        print "Waiting for the customized catalog ingest to successfully post and sync with CI Host in seconds: " + str(sleep_channel)
        time.sleep(sleep_channel)
        pps_headers = {
                 'Content-Type': 'application/json',
                 'Source-Type': 'WEB',
                 'Source-ID': '127.0.0.1',
                 }
        upm_headers = {
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            'Accept': 'application/json',
        }

        cmdc_hosts = [cfg['cmdc']['host']]
        pps_hosts = [cfg['pps']['host']]
        hosts_list = list(itertools.product(cmdc_hosts,pps_hosts,upm_hosts))
        printLog("Final list :"+ str(hosts_list),printflg)
        householdlimit = cfg['basic_feature']['households_needed']
        index = random.randint(0,householdlimit-1)
        householdid = prefix + str(index)
        contentid_list= []
        start_time_list = []
        end_time_list = []
        duration_list = []
        cDVR_service_list= ["CDVR","ALLOW-CDVR-TIME-BASED-RECORDING"]
        print cDVR_service_list
        #cDVR_service_list = json.dumps(cDVR_service_list)

    except :
        message =  "Testcase failed : Error Occured in configuration\n" + PrintException(True)
        print message 
        tims_dict = update_tims_data(tims_dict,1,message,["TC1645"])
        return tims_dict
    for (cmdc_host,pps_host,upm_host) in hosts_list :
     try:
        print "Cleaning up the household bookings and recordings before testcase execution"
        print_failedrecording_catalog(port_pps,protocol,pps_host,householdid,timeout)
        cleanup_householdid_items(port_pps,protocol,pps_host,householdid,pps_headers,timeout)
        print "### STEP2 Do the PPS Booking for the Household and Wait till the recording completes. Verify the Event is recorded successfully################################### \n \n "
        grid_response = fetch_gridRequest(catalogueId,protocol,cmdc_host,port_cmdc,serviceidlist,region,timeout,printflg=False)
        if grid_response:
          contentId_dict_all = get_contentIddict_bytitle(grid_response,eventtitle,['title'])
          if contentId_dict_all :
              event_contentId_list = sorted(contentId_dict_all.items(), key=lambda x:x[1])
              if len(event_contentId_list) >=1:
                  for items in event_contentId_list:
                        contentid_list.append(items[0])
                        start_time_list.append(items[1][0])
                        end_time_list.append(items[1][1])
                        duration_list.append(items[1][2])
                  payload1 =  """{
                        "checkConflicts": true,
                        "pvr": "nPVR",
                        "scheduleInstanceId": "%s"
                        }"""%(contentid_list[0])
              else:
                    message =  "Testcase failed : Error in retrieving First Random Content ID Dictionary"
                    print message 
                    tims_dict = update_tims_data(tims_dict,1,message,["TC1645"])
                    return tims_dict
          else:
                message =  "Testcase failed : Error in retrieving First Full Content ID Dictionary"
                print message 
                tims_dict = update_tims_data(tims_dict,1,message,["TC1645"])
                return tims_dict
        else:
             message =  "Testcase failed : Error in retrieving First Grid Response"
             print message 
             tims_dict = update_tims_data(tims_dict,1,message,["TC1645"])
             return tims_dict
        result = do_PPSbooking(port_pps,protocol,pps_host,householdid,pps_headers,payload1,contentid_list[0],timeout,printflg)
        if result == "PASS":
            time.sleep (recordingstatecheck_waittime)
            verify_booking_result,bookedcatalogresponse = verify_booking(port_pps,protocol,pps_host,householdid,contentid_list[0],timeout)
            if verify_booking_result == "PASS" :
                  print "booking is verified"
                  jsonrecordedcontent = json.loads(bookedcatalogresponse.content)
                  for items in jsonrecordedcontent:
                     recordedtitle = items['title']
                     contentplayuri = items['contentPlayUri']
            else:
                message =  "Testcase failed : Booked catalog does not have all the events"
                print message
                tims_dict = update_tims_data(tims_dict,1,message,["TC1645"])
                return tims_dict
        else:
            message =  "Testcase failed : First PPS Booking failed"
            print message 
            tims_dict = update_tims_data(tims_dict,1,message,["TC1645"])
            return tims_dict
        program_starttime = get_timedifference(start_time_list[0],printflg)
        print "Recording will start in " + str(program_starttime)+ "seconds"
        time.sleep(program_starttime)
        time.sleep(recordingstatecheck_waittime)
        #time.sleep(300)
        recordingcontentresult,recordingcontentresponse = verify_recording_state(port_pps,protocol,pps_host,householdid,contentid_list[0],timeout)
        if recordingcontentresult == "PASS":
             jsonrecordingcontent = json.loads(recordingcontentresponse.content)
             printLog("Recording Content Response for the Content Id\n" + json.dumps(json.loads(recordingcontentresponse.content),indent=4,sort_keys=False),printflg)
        else:
             message =  "Testcase failed : Recording has not started for the event"
             print message
             tims_dict = update_tims_data(tims_dict,1,message,["TC1234"])
             return tims_dict
        program_endtime = get_timedifference(end_time_list[0],printflg)
        print "Program Recording completes in "+str(program_endtime/60)+" minutes"
        time.sleep(program_endtime)
        time.sleep(recordedstatecheck_waittime)
        #time.sleep(360)
        recordedcontentresult,recordedcontentresponse = verify_recorded_state(port_pps,protocol,pps_host,householdid,contentid_list[0],timeout)
        if recordedcontentresult == "PASS":
            jsonrecordedcontent = json.loads(recordedcontentresponse.content)
            printLog("Recorded Content Response for the Content Id\n" + json.dumps(json.loads(recordedcontentresponse.content),indent=4,sort_keys=False),printflg)
            print "Recording is successful"
        else:
             message ="Recording is unsuccessful"
             print message
             tims_dict = update_tims_data(tims_dict,1,message,["TC1234"])
             return tims_dict
        print "### STEP3 disable all CDVR related services"
        deleteserviceresult = delete_HouseholdEnabledService( protocol, upm_host, port_upm, householdid, cDVR_service_list , upm_headers, timeout)
        if deleteserviceresult == "PASS":
            print "Deleting the Service for the Household is successful"
        else:
             message = "Testcase failed :Testcase failed :Failed to Delete the Service for the Household"
             print message
             tims_dict = update_tims_data(tims_dict, 1, message, ["TC1645"])
             return tims_dict
        householdservicelist = get_HouseholdEnabledServices( protocol, upm_host, port_upm, householdid, upm_headers, timeout)
        if householdservicelist :
            servicelist = json.loads(householdservicelist)
            for service in cDVR_service_list:
                if service in servicelist:
                    set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
                    message = "Testcase failed :Failed to Delete the Service for the Household"
                    print message
                    tims_dict = update_tims_data(tims_dict, 1, message, ["TC1645"])
                    return tims_dict
        else:
             set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
             message = "Testcase failed :Testcase failed :Failed to Delete the Service for the Household"
             print message
             tims_dict = update_tims_data(tims_dict, 1, message, ["TC1645"])
             return tims_dict
        print "###STEP4.Verify the event is still there in the recorded library ##########################\n\n"
        recordedcontentresult,recordedcontentresponse = verify_recorded_state(port_pps,protocol,pps_host,householdid,contentid_list[0],timeout)
        if recordedcontentresult == "PASS":
            jsonrecordedcontent = json.loads(recordedcontentresponse.content)
            for items in jsonrecordedcontent:
                recordedtitle = items['title']
                contentplayuri = items['contentPlayUri']
            printLog("Recorded Content Response for the Content Id\n" + json.dumps(json.loads(recordedcontentresponse.content),indent=4,sort_keys=False),printflg)
            print "Recording is successful"
        else:
             set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
             message ="Recording is unsuccessful"
             print message
             modify_diskQuota(cfg,protocol,upm_host,port_upm,householdid,old_diskquota,diskquota_headers_hh,timeout,printflg)
             tims_dict = update_tims_data(tims_dict,1,message,["TC1234"])
             return tims_dict
        #recordedtitle= "Event106_1 event Name"
        #contentplayuri = "http://path?recId=d0fb76f6-9b8a-4147-b60b-e6d60192777c&type=cDVR"
        print "###STEP5.Try to Playback the recorded content and verify it should not allow to play since CDVR is disabled#########################\n\n"
        playbk_rslt,playbk_msg = playback(cfg,test,abspath,port_pps,protocol,pps_host,recordedtitle,contentplayuri,householdid,pps_headers,timeout,printflg)
        if playbk_rslt == "FAIL":
            print "###STEP6.Enable back all the CDVR services ##########################\n\n"
            set_Household_enable_services = set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
            message = playbk_msg +  ", Testcase Passed"
            if set_Household_enable_services:
                householdservicelist = get_HouseholdEnabledServices(protocol, upm_host, upm_port, householdid, upm_headers, timeout)
                if householdservicelist:
                    cdvr_list_after_enable = 0
                    servicelist = json.loads(householdservicelist)
                    print "Household Service List" + str(servicelist)
                    for service in cDVR_service_list:
                         if service in servicelist:
                            cdvr_list_after_enable = cdvr_list_after_enable + 1
                    if cdvr_list_after_enable:
                        if cdvr_list_after_enable == len(cDVR_service_list):
                            print "CDVR services are enabled successfully"
                            print "###STEP7Verify playback the recorded event and see it is successfully done since CDVR services are enabled back##########################\n\n"
                            playbk_rslt,playbk_msg = playback(cfg,test,abspath,port_pps,protocol,pps_host,recordedtitle,contentplayuri,householdid,pps_headers,timeout,printflg)
                            if playbk_rslt == "PASS":
                                 set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
                                 message = playbk_msg +  ", Testcase Passed"
                                 tims_dict = update_tims_data(tims_dict,0, message, ["TC1645"])
                                 return tims_dict
                            else:
                                set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
                                message = playbk_msg + ", Testcase failed"
                                print message
                                tims_dict = update_tims_data(tims_dict,1, message, ["TC1645"])
                                return tims_dict
                        else:
                             set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
                             message = "CDVR services are not enabled successfully"
                             print message
                             tims_dict = update_tims_data(tims_dict,1, message, ["TC1645"])
                             return tims_dict
                    else:
                        message = "Testcase failed :error in retrieving the cdvr Service list  for the Household after enabling"
                        print message
                        set_HouseholdEnabledService(
                            protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                        tims_dict = update_tims_data(
                            tims_dict, 1, message, ["TC1645"])
                        return tims_dict
                else:
                    message = "Testcase failed :error is retrieving household enable services for the Household after enabling"
                    print message
                    set_HouseholdEnabledService(
                        protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                    tims_dict = update_tims_data(
                        tims_dict, 1, message, ["TC1645"])
                    return tims_dict
            else:
                 message = "Testcase failed :error is retrieving household enable services for the Household after enabling"
                 print message
                 set_HouseholdEnabledService(protocol, upm_host, upm_port, householdid, cdvr_service_list, upm_headers, timeout)
                 tims_dict = update_tims_data(tims_dict, 1, message, ["TC1645"])
                 return tims_dict
        else:
            set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
            message = playbk_msg + ", Testcase failed"
            print message
            tims_dict = update_tims_data(tims_dict,1, message, ["TC1645"])
            return tims_dict
 
     except :
             if cDVR_service_list:
                 set_HouseholdEnabledService(protocol, upm_host, port_upm, householdid, cDVR_service_list, upm_headers, timeout)
             message =  "Testcase failed : Error Occured \n" + PrintException(True)
             print message 
             tims_dict = update_tims_data(tims_dict,1,message,["TC1645"])
             return tims_dict

def playback(cfg,test,abspath,port_pps,protocol,pps_host,recordedtitle,contentplayuri,householdid,pps_headers,timeout,printflg):
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


