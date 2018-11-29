"""
The following functions are used for PPS V3 API.
"""

#from scripts.cornercase_scripts.cornercase_set1_scripts.L1commonFunctions import *
from L1commonFunctions import *
from L2commonFunctions import *
from L3commonFunctions import *
from V3_planner import cleanup_planner
import re
import json
from pip._vendor.requests.packages.urllib3 import response

def get_booking_header(plannerId):
    try:
        planner = "{\"hhId\":\"%s\"}"%plannerId
        header = {
                "x-cisco-vcs-identity":planner,
                "Content-Type":"application/json"
                }
        return header
    except Exception as e:
        print "Error in get booking headers :\n",str(e)
        return None


def get_header(plannerId):
    planner = "{\"hhId\":\"%s\"}" % plannerId
    header = {
                 "x-cisco-vcs-identity":planner,
                 "Content-Type":"application/json"
             }
    return header


def create_series_booking(cfg, plannerId, payload, timeout=2, pps_host=None, update=False):
    """
    Create a Event booking and return whole response
    :param cfg: config parameter
    :param plannerId: planner id
    :param payload: payload for booking
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return:
    """

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_header(plannerId)
        if headers is None:
            print "Unable to get the Booking headers"
            return False, None

        print "Headers :",headers

        if update:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recurrences/updateRecurrence"
            print "PPS V3 Event Booking via url : %s" % url
        else:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recurrences/createGroupRecurrence"
            print "PPS V3 Event Booking via url : %s" % url

        r = sendURL("post", url, server_timeout=timeout, header=headers, payload_content=payload)

        if r is not None:
            if r.status_code != 201 and r.status_code != 200:
                print "PPS V3 Event Booking / Update Failed"
                print r.status_code
                print r.headers
                print r.content
                return False, r
            else:
                # print "PPS V3 - Event Booking successful"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 Event booking :\n", str(e)
        return False, None


def create_event_booking(cfg, plannerId, payload, timeout=2, pps_host=None, timeBooking = False):
    """
    Create a Event booking and return whole response
    :param cfg: config parameter
    :param plannerId: planner id
    :param payload: payload for booking
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return:
    """

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_header(plannerId)
        if headers is None:
            print "Unable to get the Booking headers"
            return False, None

        print "Headers :",headers

        if timeBooking:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/bookings/createTimeBooking"
            print "PPS V3 Event Booking via url : %s" % url

        else:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/bookings/createEventBooking"
            print "PPS V3 Event Booking via url : %s" % url

        print "PAYLOAD:", payload
        r = sendURL("post", url, server_timeout=timeout, header=headers, payload_content=payload)

        
        if r is not None:    
            if r.status_code != 201:
                print "PPS V3 Event Booking Failed"
                print r.status_code
                print r.headers
                print r.content
                return False, r
            else:
                # print "PPS V3 - Event Booking successful"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 Event booking :\n", str(e)
        return False, None


def update_booking_or_recording(cfg, plannerId, itemId, pps_host=None, endGuardTime=0, startGuardTime=0, keep=None,
                                autoDeletePeriod=None, lock=None, recordingUpdate=False, timeout=2):
    """
    Update an existing booking or recording either one or more of the parameters
    :param cfg:
    :param plannerId: <Mandate>
    :param itemId:
    :param pps_host:
    :param endGuardTime:
    :param startGuardTime:
    :param keep:
    :param autoDeletePeriod:
    :param lock:
    :param timeout:
    :return:
    """
    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']
        payload = {}

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_header(plannerId)
        if headers is None:
            print "Unable to get the Booking headers"
            return False, None

        print "Headers :", headers

        payload["itemId"] = itemId

        if keep:
            payload["keep"] = keep

        if autoDeletePeriod:
            payload["autoDeletePeriod"] = autoDeletePeriod

        if lock:
            payload["lock"] = lock
        cpayload = payload
        payload = json.dumps(payload)
        if recordingUpdate:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recordings/updateRecording"
            print "PPS V3 Event Recording Update via url : %s" % url
            if cpayload.has_key("startGuardTime") or cpayload.has_key("endGuardTime"):
                print "INPUT ERROR: Can not update Guard time for recorded Events."
                return False, "Can not update Guard time for recorded Events"
        else:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/bookings/updateBooking"
            print "PPS V3 Event Booking Update via url : %s" % url

        r = sendURL("post", url, server_timeout=timeout, header=headers, payload_content=payload)

        if r is not None:
                try:
                    r.raise_for_status()
                    print "Event Recording update is successful"
                    return True, r
                except:
                    print "PPS V3 Event Recording update Failed"
                    print r.status_code
                    print r.headers
                    return False, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 Event Recording Updation :\n", str(e)
        return False, None


def update_call_booking_or_recording(cfg, plannerId, itemId, pps_host=None, endGuardTime=0, startGuardTime=0, keep=None,
                                     autoDeletePeriod=None, lock=None, recordingUpdate=False, timeout=2):
    """
    Update an existing booking or recording either one or more of the parameters
    :param cfg:
    :param plannerId: <Mandate>
    :param itemId:
    :param pps_host:
    :param endGuardTime:
    :param startGuardTime:
    :param keep:
    :param autoDeletePeriod:
    :param lock:
    :param timeout:
    :return:
    """
    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']
        payload = {}

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_header(plannerId)
        if headers is None:
            print "Unable to get the Booking headers"
            return False, None

        print "Headers :", headers

        payload["itemId"] = itemId
        payload["startGuardTime"] = startGuardTime
        payload["endGuardTime"] = endGuardTime

        if keep:
            payload["keep"] = keep

        if autoDeletePeriod:
            payload["autoDeletePeriod"] = autoDeletePeriod

        if lock:
            payload["lock"] = lock
        cpayload = payload
        payload = json.dumps(payload)
        if recordingUpdate:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recordings/updateRecording"
            print "PPS V3 Event Recording Update via url : %s" % url
            if cpayload.has_key("startGuardTime") or cpayload.has_key("endGuardTime"):
                print "INPUT ERROR: Can not update Guard time for recorded Events."
                return False, "Can not update Guard time for recorded Events"
        else:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/bookings/updateBooking"
            print "PPS V3 Event Booking Update via url : %s" % url

        r = sendURL("post", url, server_timeout=timeout, header=headers, payload_content=payload)

        if r is not None:
                try:
                    r.raise_for_status()
                    print "Event Recording update is successful"
                    return True, r
                except:
                    print "PPS V3 Event Recording update Failed"
                    print r.status_code
                    print r.headers
                    return False, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 Event Recording Updation :\n", str(e)
        return False, None


def create_booking(cfg, plannerId, channelId, startTime=0, duration=0, contentRef=None, timeout=2, pps_host=None,
                   eventRef=None, groupId=None, endGuardTime=0, startGuardTime=0, keep=None, autoDeletePeriod=None, lock=None,
                   groupType=None, channelPreference=None, canBookReruns=None, recordingsToKeep=0, timeBooking=False):
    """
    Create a event / series / time-based Booking and verify the response and return the itemId
    ChannelPreference can either be [[CHANNEL-PREFERRED, CHANNEL-ONLY]
    :param cfg:
    :param plannerId:
    :param payload:
    :param timeout:
    :param pps_host:
    :return:
    """
    payload = {}
    payload['channel'] = channelId
    payload['startTime'] = startTime
    payload['duration'] = duration
    
    contentRef and payload.update(dict(contentRef=contentRef))
    eventRef and payload.update(dict(eventRef=eventRef))
    groupId and payload.update(dict(groupId=groupId))
    endGuardTime and payload.update(dict(endGuardTime=endGuardTime))
    startGuardTime and payload.update(dict(startGuardTime=startGuardTime))
    keep and payload.update(dict(keep=keep))
    autoDeletePeriod and payload.update(dict(autoDeletePeriod=autoDeletePeriod))
    lock and payload.update(dict(lock=lock))
    groupType and payload.update(dict(groupType=groupType))
    channelPreference and payload.update(dict(channelPreference=channelPreference))
    canBookReruns and payload.update(dict(canBookReruns=canBookReruns))
    recordingsToKeep and payload.update(dict(recordingsToKeep=recordingsToKeep))


    if timeBooking or groupType:    # FOR TIME BOOKING, RECURRENCE DOESNT NEED CONTENT REF
        if payload.has_key("contentRef"):
            del payload["contentRef"]

    if groupType:
        if "duration" in payload.keys():
            del payload['duration']         # RECURRENCE BOOKING DOES NOT NEED DURATION, START TIME
        if "startTime" in payload.keys():
            del payload['startTime']

        payload = json.dumps(payload)
        res, response = create_series_booking(cfg, plannerId, payload, pps_host)
    elif timeBooking:
        payload = json.dumps(payload)
        res, response = create_event_booking(cfg, plannerId, payload, timeout, pps_host, timeBooking=True)
    else:
        payload = json.dumps(payload)
        res, response = create_event_booking(cfg, plannerId, payload, pps_host)

    if res:
        resp = json.loads(response.content)
        if resp['status'] == "CREATED" and resp['itemId']:
            print "PPS V3 Event Booking successful "
            return True, resp['itemId']
        elif resp['status'] == "EXISTING":
            print "Conflict - Event is already exists"
            return False, response
        else:
            print "PPS Booking response Status :", resp['status']
            return False, response
    else:
        return False, response


def update_series_booking(cfg, plannerId, channelId, timeout=2, pps_host=None, groupId=None, endGuardTime=0,
                          startGuardTime=0, keep=None, autoDeletePeriod=None, lock=None, groupType=None,
                          channelPreference=None, canBookReruns=None, recordingsToKeep=0):
    """
    Create a event Booking and verify the response and return the itemid
    ChannelPreference can either be [[CHANNEL-PREFERRED, CHANNEL-ONLY]
    :param cfg:
    :param plannerId:
    :param payload:
    :param timeout:
    :param pps_host:
    :return:
    """
    local_args = locals()
    payload = {}
    for i, j in zip(local_args.keys(), local_args.values()):

        if i in ['startGuardTime', 'endGuardTime']:
            i = sec2interval(i)

        if local_args[i]:
            payload[i] = j

    payload = json.dumps(payload)
    res, response = create_series_booking(cfg, plannerId, payload, update=True)

    if res:
        resp = json.loads(response.content)
        if resp['status'] == "UPDATED" and resp['itemId']:
            print "PPS V3 Event Booking UPDATE successful"
            return True, resp['itemId']
        elif resp['status'] == "EXISTING":
            print "Conflict - Event Update requires some change"
            return False, response
        else:
            print "PPS Booking response Status :", resp['status']
            return False, None
    else:
        return False, response


def get_booking(cfg, plannerId, itemid, timeout=2, pps_host=None, recurrence=False):
    """
    Get the All the bookings of a Planner Id for Indie events, & recurrence bookings.
    :param cfg:
    :param plannerId:
    :param state:
    :param timeout:
    :param pps_host:
    :return:
    """

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None

        if recurrence:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recurrences/getRecurrence?itemId" \
                                                                      "=%s"%itemid
            print "Get recurrence via URL : ", url

        else:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/getBooking?itemId=%s"%itemid
            print "Get Booking via URL : ", url

        r = sendURL("get", url, server_timeout=timeout, header=header)

        if r is not None:
            if r.status_code != 200:
                print "PPS V3 Unable to get booking"
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3 got the booking"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 get Booking :\n", str(e)
        return False, None


def is_itemids_booked(cfg, planner_id, bkin_itms_lst, timeout):
    """
    Create a Event booking and return whole response
    :param cfg: config parameter
    :param plannerId: planner id
    :param bkin_itms_lst: Booking Items List for validating
    :param timeout: timeout value
    :return: function_status, response
    """

    try:
        for item in bkin_itms_lst:
            result, response = get_booking(cfg, planner_id, item, timeout)

            if result:
                res_dict = json.loads(response.content)
                # single call pick the first value
                res_dict = res_dict["bookings"][0]
                assert res_dict.get("state") == "BOOKED", (
                    "Test case Failed: Event booked response"
                    " for Event is not BOOKED"
                )
                return True, response
        return False, None
    except Exception as e:
        print "Error in PPS V3 booking state :\n", str(e)
        return False, None


def get_bookings(cfg, plannerId, timeout=2, pps_host=None, sortOrder="CREATE-DATE", recordingState="ALL", limit=999,
                 recurrence=False):
    """
    Get the All the bookings of a Planner Id. By default it is displayed by Create-Date sorted manner.
    Additional options for sorting are [CREATE-DATE, START-TIME, CREATE-DATE-REVERSE, START-TIME-REVERSE]
    Can be sorted based on the recordingState as well. Options are [ALL, RECORDING, NOT-STARTED]
    :param cfg:
    :param plannerId:
    :param state:
    :param timeout:
    :param pps_host:
    :return:
    """

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None
        if recurrence:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recurrences/getRecurrences"

        else:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/getBookings?sort=%s&" \
                                                                      "recordingState=%s&limit=%d" % (sortOrder,
                                                                                                      recordingState,
                                                                                                      limit)
        print "Get request sent via URL: ", url
        r = sendURL("get", url, server_timeout=timeout, header=header)
        print "Get Bookings via URL : ", url

        if r is not None:
            if r.status_code != 200:
                print "PPS V3 Unable to get bookings"
                print r.status_code
                print r.headers
                return False, r
            elif r.status_code == 200 and not r.json(): # empty dictionary
                return False, None
            else:
                print "PPS V3 got the bookings"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 get Bookings :\n", str(e)
        return False, None


def find_bookings_by_start_time(cfg, channel, starttime, plannerid, timeout=2, pps_host=None):
    """
    Get a booking based on the start time
    :param cfg: config parameter
    :param channel: channel number as string
    :param starttime: starttime of booking, it should be in ISO format
    :param plannerid: planner id
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return: (True, Booking response) if success else (False, None)
    """
    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerid)
        if header is None:
            print "Unable to get the headers"
            return False, None

        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/bookings/findBookingsByStartTime?" \
                                                                  "channel=%s&eventStartTime=%s" %(channel, starttime)

        r = sendURL("get", url, server_timeout=timeout, header=header)
        print "Find Bookings by start time via URL : ", url

        if r is not None:
            if r.status_code != 200:
                print "PPS V3 Unable to find bookings by start time"
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3 - found the bookings by start time"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 find Bookings by start time :\n", str(e)
        return False, None


def find_bookings_by_contentref(cfg, plannerId, contentref, timeout=2, pps_host=None):
    """
    Find the bookings based on the content ref
    :param cfg: config parameter
    :param contentref: contentRef of the booked content
    :param plannerId: planner id
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return: (True, Booking response) if success else (False, None)
    """
    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None

        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/findBookingsByContentRef?" \
                                                                  "contentRef=%s" % (contentref)

        r = sendURL("get", url, server_timeout=timeout, header=header)
        print "Find Bookings by contentref via URL : ", url

        if r is not None:
            if r.status_code != 200:
                print "PPS V3 Unable to find bookings by contentref"
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3 - found the bookings by contentRef"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 find Bookings by contentref :\n", str(e)
        return False, None


def is_cont_ref_list_booked(cfg, plannerId, cont_refs, timeout=5):
    """
    Get Content Ref List as input and Call Find Booking by ContRef API

    - Used to Check Booked state using ContRef
    - Used in Series Booking
    :return True when all episodes are booked else False
    """

    if not isinstance(cont_refs, list):
        cont_refs = [cont_refs]

    bkd_lst = []
    for content_ref in cont_refs:
        result, response = is_cont_ref_booked(cfg, plannerId, content_ref, timeout)
        if result:
            bkd_lst.append(True)
        else:
            return False, response
        
    if len(bkd_lst) == len(cont_refs):
        return True, None
    return False, None

def is_cont_ref_booked(cfg, plannerId, cont_ref, timeout=5):
    """
    Get Content Ref as input and Call Find Booking by ContRef API

    - Used to Check Booked state using ContRef
    - Used in Series Booking
    :return response with response boolean status
    """

    result, response = find_bookings_by_contentref(
        cfg, plannerId, cont_ref, timeout)
    print "[INFO: ] booking by content ref result status ", result
    print "[INFO: ] booking by content ref response ", response.content
    if result:
        res_dict = json.loads(response.content)
        res_bkg_lst = res_dict.get("bookings")
        if res_bkg_lst and len(res_bkg_lst):
            # Per call single Content Ref.
            # Take First Value for Validation
            bk_item = res_bkg_lst[0]
            print "[INFO: ] Booked Item: ", bk_item
            if bk_item.get("state") == "BOOKED":
                return True, response
            else:
                return False, response
        else:
            return False, response
    else:
        return False, response


def find_recurrences_by_groupId_Type(cfg, channel, starttime, plannerid, groupId, groupType, timeout=2, pps_host=None):
    """
    Get a recurrence booking based on the groupId & groupType
    :param cfg: config parameter
    :param channel: channel number as string
    :param groupId: string
    :param groupType: string
    :param plannerid: planner id
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return: (True, Booking response) if success else (False, None)
    """
    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerid)
        if header is None:
            print "Unable to get the headers"
            return False, None

        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recurrences/findGroupRecurrence?" \
                                                                  "groupId=%s&groupType=%s" %(groupId, groupType)

        r = sendURL("get", url, server_timeout=timeout, header=header)
        print "Find Recurrences by groupId & groupType via URL : ", url

        if r is not None:
            if r.status_code != 200:
                print "PPS V3 Unable to find bookings by groupId & groupType"
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3 - found the bookings by groupId & groupType"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 find Bookings by groupId & groupType:\n", str(e)
        return False, None


def delete_booking(cfg, plannerId, itemid, timeout=2, pps_host=None, recurrence=False):
    """
    Delete a Event booking or Series booking based on the payload passed
    :param cfg:
    :param plannerId:
    :param timeout:
    :param printflg:
    :param pps_host:
    :return:
    """

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_header(plannerId)
        if headers is None:
            print "Unable to get the Booking headers"
            return False, None
	payload = {}
        payload["itemId"] = itemid
	# Converting to json format before packing into the request.
        payload = json.dumps(payload)
        print "Headers :",headers
        if recurrence:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recurrences/deleteRecurrence"
        else:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/bookings/deleteBooking"

        r = sendURL("post", url, server_timeout=timeout, header=headers, payload_content=payload)
        print "Delete booking via URL :", url

        if r is not None:
            if r.status_code != 204 and r.status_code != 200:
                print "PPS V3 Delete_Booking Failed"
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3 - Delete_Booking successful"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 Delete_booking :\n", str(e)
        return False, None


def get_failures(cfg, plannerId, timeout=2, pps_host=None, limit=999):
    """
    Get the failures of Planner
    :param cfg:
    :param plannerId:
    :param timeout:
    :param pps_host:
    :return:
    """
    protocol = cfg['protocol']
    pps_port = cfg['pps']['port']

    if pps_host is None:
        pps_host = cfg['pps']['host']

    header = get_header(plannerId)
    if header is None:
        print "Unable to get the headers"
        return False, None

    url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/failures/getFailures?limit=%d" % limit
    print "Get failures with url :",url
    r = sendURL("get", url, server_timeout=timeout, header=header)

    if r.status_code == 200:
        return r
    else:
        return False


def get_failure(cfg, plannerId, itemId, timeout=2, pps_host=None):
    """
    Get the particular failure based on itemId of Planner
    :param cfg:
    :param plannerId:
    :param timeout:
    :param pps_host:
    :return:
    """
    protocol = cfg['protocol']
    pps_port = cfg['pps']['port']

    if pps_host is None:
        pps_host = cfg['pps']['host']

    header = get_header(plannerId)
    if header is None:
        print "Unable to get the headers"
        return False, None

    url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/failures/getFailure?itemId=%s" % itemId
    print "Get failures with url :",url
    r = sendURL("get", url, server_timeout=timeout, header=header)

    if r.status_code == 200:
        return r
    else:
        return False


def delete_failure(cfg, plannerId, itemId, timeout=2, pps_host=None):
    """
    Get the particular failure based on itemId of Planner
    :param cfg:
    :param plannerId:
    :param timeout:
    :param pps_host:
    :return:
    """
    protocol = cfg['protocol']
    pps_port = cfg['pps']['port']

    if pps_host is None:
        pps_host = cfg['pps']['host']

    header = get_header(plannerId)
    if header is None:
        print "Unable to get the headers"
        return False, None

    url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/failures/deleteFailure?itemId=%s" % itemId
    print "Delete failures with url :", url
    r = sendURL("delete", url, server_timeout=timeout, header=header)

    if r.status_code == 200:
        return True, None
    else:
        return False, r


def delete_allbookingsinGroup(cfg, plannerId, itemId, groupId, groupType, timeout=2, pps_host=None):
    """
    Delete all bookings in a group recurrence
    :param cfg:
    :param plannerId:
    :param timeout:
    :param pps_host:
    :return:
    """
    protocol = cfg['protocol']
    pps_port = cfg['pps']['port']

    if pps_host is None:
        pps_host = cfg['pps']['host']

    header = get_header(plannerId)
    if header is None:
        print "Unable to get the headers"
        return False, None

    payload = {}
    payload["groupId"] = groupId
    payload["groupType"] = groupType

    url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/utils/deleteAllBookingsInGroup"
    print "Delete All bookings in group with url :", url
    r = sendURL("post", url, server_timeout=timeout, header=header, payload_content=payload)

    if r.status_code == 200:
        return True, None
    else:
        return False, r


def delete_recurrencebyGroupId(cfg, plannerId, itemId, groupId, groupType, timeout=2, pps_host=None):
    """
    Delete the particular booking based on GroupID
    :param cfg:
    :param plannerId:
    :param timeout:
    :param pps_host:
    :return:
    """
    protocol = cfg['protocol']
    pps_port = cfg['pps']['port']

    if pps_host is None:
        pps_host = cfg['pps']['host']

    header = get_header(plannerId)
    if header is None:
        print "Unable to get the headers"
        return False, None

    payload = {}
    payload["groupId"] = groupId
    payload["groupType"] = groupType
    # Fix for 400 bad request error.
    payload = json.dumps(payload)

    url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/utils/deleteRecurrenceByGroupId"
    print "Delete Recurrence bookings in group with url :", url
    r = sendURL("post", url, server_timeout=timeout, header=header, payload_content=payload)

    if r.status_code == 200:
        return True, None
    else:
        return False, r


def verify_failed(cfg, plannerId, contentRef, timeout=2, pps_host=None):
    """
    Verify that the contentRef is in failed catalog for the planner
    :param cfg:
    :param plannerId:
    :param contentRef2:
    :param timeout:
    :param pps_host:
    :return:
    """
    resp = get_failures(cfg, plannerId, timeout, pps_host)
    if resp:
        out = json.loads(resp.content)
        if "failures" in out:
            if len(out["failures"]) != 0:
                for cont in out["failures"]:
                    if cont['contentRef'] == contentRef:
                        return True, cont
            else:
                print "failures block is empty"
                return False, None
        else:
            print "failures block is not present in the response"
            return False, None
    else:
        print "Unable to verify the content is in Failed state"
        return False, None


def find_booking_conflicts(cfg, plannerId, channel, startGuardTime = "PT0S", endGuardTime = "PT0S", eventDuration = 0,
                           eventStartTime = 0, pps_host=None, timeout=2):
    """
    This returns all of the bookings that currently conflict with the event referenced by the supplied query parameters.
    Guard times will be included in the conflict detection according to system policy.
    :param cfg:
    :param plannerId:
    :param channel:
    :param startGuardTime:
    :param endGuardTime:
    :param eventDuration:
    :param eventStartTime:
    :return:
    """

    protocol = cfg['protocol']
    pps_port = cfg['pps']['port']

    if pps_host is None:
        pps_host = cfg['pps']['host']

    header = get_header(plannerId)
    if header is None:
        print "Unable to get the headers"
        return False, None

    if not eventDuration.isdigit():
        eventDuration = str(epoch2iso(eventDuration))

    if not eventStartTime.isdigit():
        eventStartTime = str(epoch2iso(eventStartTime))

    if startGuardTime != "PT0S":
        startGuardTime = str(sec2interval(startGuardTime*60))

    if endGuardTime != "PT0S":
        endGuardTime = str(sec2interval(endGuardTime*60))


    url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/utils/findBookingConflicts?channel=%s&event" \
                                                              "Duration=%s&eventStartTime=%s&startGuardTime=%s&end" \
                                                              "GuardTime=%s" % (channel, eventDuration, eventStartTime,
                                                                                startGuardTime, endGuardTime)
    print "Find booking conflicts with url :", url
    r = sendURL("post", url, server_timeout=timeout, header=header)

    if r.status_code == 200:
        return True, None
    else:
        return False, r


# Deprecated
def get_contentRef_from_groupId(cfg, plannerId, groupid, timeout=2, seriesResolution_host=None):
    """
    Get the Content Ref from the Group Id
    :param cfg:
    :param plannerId:
    :param groupid:
    :param timeout:
    :param planner_host:
    :return:
    """
    try:
        protocol = cfg['protocol']
        planner_port = cfg['seriesResolution']['port']

        if seriesResolution_host is None:
            planner_host = cfg['seriesResolution']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None

        url = protocol + "://" + planner_host + ":" + str(planner_port) + "/planner/seriesResolution/groupContents" \
                                                                          "AndInstances?groupId=%s" % groupid

        r = sendURL("get", url, server_timeout=timeout, header=header)

        if r is not None:
            if r.status_code != 201:
                print "PPS V3 Unable to Content Ref via url %s" % url
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3. Got the ContentRef from the GroupId"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in get ContentRef from GroupId :\n", str(e)

# Deprecated
def get_groupId_from_contentRef(cfg, plannerId, contentRef, timeout=2, seriesResolution_host=None):
    try:
        protocol = cfg['protocol']
        planner_port = cfg['seriesResolution']['port']

        if seriesResolution_host is None:
            planner_host = cfg['seriesResolution']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None

        url = protocol + "://" + planner_host + ":" + str(planner_port) + "/planner/seriesResolution/contentGroups?" \
                                                                          "contentRef=%s" % contentRef

        r = sendURL("get", url, server_timeout=timeout, header=header)

        if r is not None:
            if r.status_code != 201:
                print "PPS V3 Unable to Group ID via url %s" % url
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3. Got the Group ID for the Content ref :", contentRef
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in get Groupid from ContentRef :\n", str(e)

# Deprecated
def get_contentRef_of_groupId(cfg, plannerId, groupid, timeout=2, seriesResolution_host=None):
    """
    To get the list of contentRefs associated with a groupId
    Return the list of episode contentRefs of the GroupId specified.
    :param cfg:
    :param plannerId:
    :param groupid:
    :param timeout:
    :param seriesResolution_host:
    :return:
    """
    res, resp = get_contentRef_from_groupId(cfg, plannerId, groupid, timeout=timeout,
                                            seriesResolution_host=seriesResolution_host)
    if res:
        contents = json.loads(resp.content)
        all_content_ids = []
        if contents:
            if contents["contentGroupId"] == groupid:
                for cont in contents["contents"]:
                    all_content_ids.append(cont['contentRef'])
            else:
                print "Group id in the Response doesn't match with the one supplied."
                print "Group id in Response :", contents["contentGroupId"]
                return False, resp

            if all_content_ids:
                return True, all_content_ids
            else:
                print "There is no episode associated with the GroupId"
                return False, resp
        else:
            print "Response from seriesResolution is empty"
            return False, None

# Deprecated
def get_groupId_of_contentRef(cfg, plannerId, contentRef, timeout=2, seriesResolution_host=None):
    """
    To get the list of GroupId associated with a contentRef.
    :param cfg:
    :param plannerId:
    :param groupid:
    :param timeout:
    :param seriesResolution_host:
    :return:
    """
    ret, resp = get_groupId_from_contentRef(cfg, plannerId, contentRef, timeout=timeout,
                                            seriesResolution_host=seriesResolution_host)
    if ret:
        contents = json.loads(resp.content)
        all_group_ids = []
        if contents:
            if contents["contentRef"] == contentRef:
                for cont in contents["groups"]:
                    all_group_ids.append(cont['groupId'])
            else:
                print "ContentRef in the Response doesn't match with the one supplied."
                print "ContentRef in Response :", contents["contentRef"]
                return False, resp

            if all_group_ids:
                return True, all_group_ids
            else:
                print "There is no group Id associated with the contentRef"
                return False, resp
        else:
            print "Response from seriesResolution is empty"
            return False, None


def get_recording(cfg, plannerId, itemid, timeout=2, pps_host=None):
    """
    Get the All the Recording of a Planner with the item id
    :param cfg: config parameter
    :param plannerId: planner id
    :param itemid: item id of the recording to get
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return: (True, Response) if success else (False, None)
    """

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None
        rec_details = None
        res, resp = get_recordings(cfg, plannerId, timeout=timeout)
        print "[INFO: ] get recordings response status ", res
        print "[INFO: ] get recordings response ", resp
        if res and resp:
            r = json.loads(resp.content)
            print "Get recordings response:"
            print r
            for i in r['recordings']:
                if i['itemId'] == itemid:
                    rec_details = i

        if rec_details:
            return True, rec_details
        else:
            return False, None

        '''
        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recordings/getRecording?itemId=%s" %\
                                                                  itemid
        print "Get Recording via URL : ", url

        r = sendURL("get", url, server_timeout=timeout, header=header)

        if r is not None:
            if r.status_code != 200:
                print "PPS V3 Unable to get Recording"
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3 got the Recording"
                return True, r
        else:
            return False, None
        '''

    except Exception as e:
        print "Error in PPS V3 get Recording:\n", str(e)
        return False, None

def get_recordings(cfg, plannerId, sort = "START-TIME", limit=999, timeout=2, pps_host=None):
    """
    Get all the Recordings of a Planner Id. Can be sorted in either ways - (START-TIME, START-TIME-REVERSE)
    limit can be set greater than 1, lesser than 1000.
    :param cfg: config parameter
    :param plannerId: planner id
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return: (True, response) if success else (False, None)
    """
    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None

        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recordings/getRecordings?sort=%s&" \
                                                                  "limit=%d" % (sort, limit)
        print "Get Recordings of planner via URL:",url
        print "Get Recordings request header:", header
        r = sendURL("get", url, server_timeout=timeout, header=header)
        print "[INFO: ] get recordings response ", r
        print "[INFO: ] get recordings response ", r.content

        if r is not None:
            if r.status_code != 200:
                print "PPS V3 Unable to get the Recordings via url %s" %url
                print r.status_code
                print r.headers
                return False, r
            elif r.status_code == 200 and not r.json():
                return False, None
            else:
                print "PPS V3. Got the recording of the planner %s"%plannerId
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 get Recording :\n", str(e)
        return False, None


def get_count(cfg, plannerId, pps_host=None, recurrence=False, bookings=False, failure=False, timeout=2):
    """
    To get count for recordings, bookings for both indie, & recurrences.
    By default, it returns count of recordings present in a planner.
    :param cfg:
    :param plannerId:
    :recurrence:
    :bookings:
    :recordings:
    :return:
    """
    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None

        if recurrence:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recurrences/countRecurrences"

            print "Get recurrence count via URL : ", url

        elif bookings:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/bookings/countBookings"
            print "Get Booking count via URL : ", url

        elif failure:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/failures/countFailures"
            print "Get Failures count of planner via URL:", url

        else:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recordings/countRecordings"
            print "Get Recordings count of planner via URL:", url

        r = sendURL("get", url, server_timeout=timeout, header=header)

        if r is not None:
            if r.status_code != 200:
                print "PPS V3 Unable to get the count via url %s" % url
                print r.status_code
                print r.headers
                return False, r
            else:
                r = json.loads(r.content)
                r = r['count']
                print "PPS V3. Got the count of the planner %s" % plannerId
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 get count :\n", str(e)
        return False, None


# Deprecated
def get_metadata_of_recording(cfg, plannerId, timeout=2, contendId=None, location_url = None, pps_host=None):
    """
    Get the metadate of the recording from the location url in the response of booking
    :param cfg:
    :param plannerId:
    :param contendId:
    :param location_url:
    :param timeout:
    :param pps_host:
    :return:
    """
    try:
        if location_url is None:
            protocol = cfg['protocol']
            pps_port = cfg['pps']['port']

            if pps_host is None:
                pps_host = cfg['pps']['host']

            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/households/"+str(plannerId)+"/catalog/"+\
                  str(contendId)

        else:
            url = location_url

        r = sendURL("get", url, server_timeout=timeout)

        if r is not None:
            if r.status_code != 201:
                print "PPS V3 Unable to get metadata of Recordings via url %s" %url
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3. Got the Metadata of Recording : %s" %contendId
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 get Metadata of Recording :\n", str(e)
        return False, None


def delete_recording(cfg, plannerId, itemids, timeout=2, pps_host=None):
    """
    Delete the recording based on the Itemid supplied
    :param cfg: config parameter
    :param plannerId: planner id
    :param itemid: item id of recording to delete
    :param timeout: timeout value
    :param pps_host: pps host(optional)
    :return: True if all the recordings are deleted else False
    """

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_booking_header(plannerId)
        if headers is None:
            print "Unable to get the booking headers"
            return False

        if not isinstance(itemids, list):
            itemids = [itemids]

        delete_fail = []
        delete_pass = []

        for itemid in itemids:
            payload = dict(itemId=itemid)
            payload = json.dumps(payload)
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recordings/deleteRecording"
            print "Delete the Recording with url: %s\npayload: %s\nheaders: %s" %(url, payload, headers)

            r = sendURL("post", url, server_timeout=timeout, header=headers, payload_content=payload)

            if r is not None:
                if r.status_code != 204: #todo: response would be 200 as per api document
                    print "Unable to Delete the Recording %s"%itemid
                    print r.status_code
                    print r.headers
                    delete_fail.append(itemid)
                else:
                    print "PPS V3 - Delete Recording successful"
                    delete_pass.append(itemid)
            else:
                delete_fail.append(itemid)

        if not delete_fail and len(delete_pass) == len(itemids):
            print "All recordings got Deleted successfully"
            return True
        else:
            print "Following Recordings were not deleted"
            print delete_fail
            return False

    except Exception as e:
        print "Error in PPS V3 Delete Recording:\n", str(e)
        return False


def verify_booking(cfg, plannerId, itemids, isRecurrence=False, timeout=2, pps_host=None):
    """
    Verify the item is in booking state.
    The content is counted irrespective of recordingInProgress state
    :param cfg: config parameter
    :param plannerId: planner id
    :param itemids: itemids
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return:
    """

    if not isinstance(itemids, list):
        itemids = [itemids]

    book_pass =[]
    book_fail=[]
    bookings_result, bookings_response = get_bookings(cfg, plannerId, recurrence=isRecurrence)
    if bookings_result:
        allBookings = json.loads(bookings_response.content)
    else:
        print "Unable to get bookings: %s" % bookings_response.content
        return False
        
    for itemid in itemids:
        found = False
        if "bookings" in allBookings:
            contents = allBookings["bookings"] 
            for cont in contents:
                if cont["itemId"] == itemid:
                    found = True
                    if cont["recordingInProgress"] == False or cont["recordingInProgress"] == True:
                        book_pass.append(itemid)
                    else:
                        book_fail.append(itemid)
            if found is False:
                book_fail.append(itemid)
        else:
            print "Bookings response doesn't have the bookings block for itemid %s" %itemid
            book_fail.append(itemid)

    if not book_fail and len(book_pass) == len(itemids):
        print "All the itemIds are in booking state"
        return True
    else:
        print "Some itemIds are not in booking state: ", book_fail
        print "The following itemIds are in booked state: ", book_pass
        print "item ids:", itemids 
        print "ALL bookings for Diag: ", allBookings
        print "Failures for Diag:"
        for itemId in itemids:
            result = get_failure(cfg, plannerId, itemId)
            if result:
                print "ERROR: failure for item id:", itemId
                print r.content
            else:
                print "INFO: No failure for item id:", itemId
        return False
    

def verify_recording(cfg, plannerId, itemids, timeout=2, pps_host=None):
    """
        Verify the content is in recording state.
        :param cfg: config parameter
        :param plannerId: planner id
        :param itemids: item id to verify
        :param timeout: timeout value
        :param pps_host: pps host <optional>
        :return: True if success else False
        """

    if not isinstance(itemids, list):
        itemids = [itemids]

    recording_pass = []
    recording_fail = []
    for itemid in itemids:
        result, responseDict = get_recording(cfg, plannerId, itemid, timeout=timeout, pps_host=pps_host)

        if result:
            if responseDict["isRecordingComplete"] is False:
                    recording_pass.append(itemid)
            else:
                    recording_fail.append(itemid)
        else:
            recording_fail.append(itemid)

    if not recording_fail and len(recording_pass) == len(itemids):
        print "All the itemids are in Recording state"
        return True
    else:
        print "Some itemids are not in recording state: ", recording_fail
        return False


def verify_inprog_rec(cfg, plannerId, itemids, timeout=2, pps_host=None):
    """
        Verify the content is in recording state.
        :param cfg: config parameter
        :param plannerId: planner id
        :param itemids: item id to verify
        :param timeout: timeout value
        :param pps_host: pps host <optional>
        :return: True if success else False
    """

    if not isinstance(itemids, list):
        itemids = [itemids]

    recording_pass = []
    recording_fail = []
    for itemid in itemids:
        result, responseDict = get_recording(cfg, plannerId, itemid, timeout=timeout, pps_host=pps_host)
        print "[INFO: ] Fetch Recording Detail response status ", result
        print "[INFO: ] Fetch Recording Detail ", responseDict

        if result:
            if responseDict.get("isRecordingComplete") is False and responseDict.get("partial") is True:
                recording_pass.append(itemid)
            else:
                recording_fail.append(itemid)
        else:
            recording_fail.append(itemid)

    if not recording_fail and len(recording_pass) == len(itemids):
        print "All the itemids are in Recording state"
        return True
    else:
        print "Some itemids are not in recording state: ", recording_fail
        return False


def get_content_playBackUri(cfg, itemIdList, householdIdList, timeout=2):
    """
    To get the list of contentplayURI for a list of contentIds and list of household ID.
    :param cfg:
    :param itemIdList:
    :param householdIdList:
    :param timeout:
    :return:
    """
    try:
        contentPlaybackUriList = []
        household_counter = 0
        contentplayback_counter = 0
        if not isinstance(householdIdList, list):
            householdIdList = [ householdIdList ]
        if not isinstance(itemIdList, list):
            itemIdList = [ itemIdList ]
            
        for householdid in householdIdList:
            for itemid in itemIdList:
                result, responseDict = get_recording(cfg, householdid, itemid, timeout=timeout)
                print "ResponseDict:", responseDict
                if result:
                    _scheduleId = responseDict['schedulingId']
                    contentPlaybackUriList.append(_scheduleId)
                    contentplayback_counter += 1
                else:
                    print "unable to get recording details for item id: %s for household: %s" %(itemid, householdid)
                
            
        #=======================================================================
        # for householdid, itemid in zip(householdIdList, itemIdList):
        #     result, responseDict = get_recording(cfg, householdid, itemid, timeout=timeout)
        #     print "ResponseDict:", responseDict
        #     if result:
        #         _scheduleId = responseDict['schedulingId']
        #         contentPlaybackUriList.append(_scheduleId)
        #         contentplayback_counter += 1
        #     else:
        #         print "unable to get recording details for item id: %s for household: %s" %(itemid, householdid)
        #=======================================================================

        if contentplayback_counter == len(itemIdList):
            return contentPlaybackUriList
        else:
            print "unable to get content playback uri for all the households", contentPlaybackUriList
            return None

    except Exception as e:
        print "Exception in get_content_playBackUri:", str(e)
        return None


def verify_recorded(cfg, plannerId, itemids, timeout=2, pps_host=None):
    """
    Verify the content is in recording state.
    :param cfg: config paratmeter
    :param plannerId: planner id
    :param itemids: item id to verify
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return: True if success else False
    """

    if not isinstance(itemids, list):
        itemids = [itemids]

    recorded_pass = []
    recorded_fail = []
    for itemid in itemids:
        result, responseDict = get_recording(cfg, plannerId, itemid, timeout=timeout, pps_host=pps_host)

        if result:
            if responseDict["isRecordingComplete"] is False:
                    recorded_pass.append(itemid)
            else:
                    recorded_pass.append(itemid)
        else:
            recorded_fail.append(itemid)

    if not recorded_fail and len(recorded_pass) == len(itemids):
        print "All the itemids are in Recorded state"
        return True
    else:
        print "Some itemdids are not in recorded state : ", recorded_fail
        return False


def verify_rec_complte(cfg, plannerId, itemids, timeout=2, pps_host=None):
    """
        Verify the content is recorded.
        :param cfg: config paratmeter
        :param plannerId: planner id
        :param itemids: item id to verify
        :param timeout: timeout value
        :param pps_host: pps host <optional>
        :return: True if success else False
    """

    if not isinstance(itemids, list):
        itemids = [itemids]

    recorded_pass = []
    recorded_fail = []
    for itemid in itemids:
        result, responseDict = get_recording(
            cfg, plannerId, itemid, timeout=timeout, pps_host=pps_host)
        print "[INFO: ] recording complete response ", responseDict
        print "[INFO: ] recording complete response status ", result

        if result:
            if responseDict.get("isRecordingComplete") is True:
                recorded_pass.append(itemid)
            else:
                recorded_fail.append(itemid)
        else:
            recorded_fail.append(itemid)

    if not recorded_fail and len(recorded_pass) == len(itemids):
        print "All the itemids are in Recorded state"
        return True
    else:
        print "Some itemdids are not in recorded state : ", recorded_fail
        return False


'''def interval2sec(duration):
    try:
        try:
            d = datetime.datetime.strptime(duration, 'PT%HH%MM%SS')
            total = (d.hour * 3600) + (d.minute * 60) + d.second
            return total
        except:
            pass

        try:
            d = datetime.datetime.strptime(duration, 'PT%MM%SS')
            total = (d.hour * 3600) + (d.minute * 60) + d.second
            return total
        except:
            pass

        try:
            d = datetime.datetime.strptime(duration, 'PT%SS')
            total = (d.hour * 3600) + (d.minute * 60) + d.second
            return total
        except:
            pass

        try:
            d = datetime.datetime.strptime(duration, 'PT%MM')
            total = (d.hour * 3600) + (d.minute * 60) + d.second
            return total
        except:
            pass

        try:
            d = datetime.datetime.strptime(duration, 'PT%HH')
            total = (d.hour * 3600) + (d.minute * 60) + d.second
            return total
        except:
            pass

    except:
        print "Unable to convert the PT time to seconds"
        return False'''

def interval2sec(duration):

    try:
        # reg = r'(\d{2}[A-Z])'
        reg = r'([0-9]+[A-Z])'

        mtch = re.findall(reg, duration)
        hh = mm = ss = dd = 0
        for mt in mtch:
            # print mt
            if mt.endswith("H"):
                hh = 3600 * int(mt.replace("H", ""))
            if mt.endswith("M"):
                mm = 60 * int(mt.replace("M", ""))

            if mt.endswith("S"):
                ss = int(mt.replace("S", ""))

            if mt.endswith("D"):
                dd = int(mt.replace("D", ""))
                return dd

        total_sec = hh + mm + ss

        #print "Total sec :", total_sec
        return total_sec
    except Exception as e:
        print "Error in interval2sec.\n", str(e)
        return False


def sec2interval(seconds):
    '''if type(seconds) is int:
        return time.strftime('PT%HH%MM%SS', time.gmtime(seconds))
    else:
        return False'''

    hh = seconds / 3600
    #print hh
    #seconds = seconds % 60
    #print ">>", seconds
    mm = (seconds % 3600) / 60
    #print mm
    seconds = seconds % 60
    #print seconds

    return "PT%02dH%02dM%02dS"%(hh,mm,seconds)



def get_contentref_details(contents):
    """

    :param contents:
    :return: [('program-1497248599', 1497248779, 1497249079, 300, 'program-149724~485992'),
              ('program-1497248600', 1497249079, 1497249379, 300, 'program-149724~486002')]
    """
    final_list=[]
    for cont in contents:
        temp_list = []
        contref = cont[0]
        strtTime = iso2epoch(cont[1])
        duration = interval2sec(cont[2])
        endTime = strtTime + duration

        temp_list.append(contref)
        temp_list.append(strtTime)
        temp_list.append(endTime)
        temp_list.append(duration)

        if len(cont) > 3:
            temp_list.append(cont[3])

        final_list.append(tuple(temp_list))

    return final_list


def get_contentref_details_series(series):
    """

    :param series:
    :return: [('program-1497248601', 1497248601, 1497248781, 180, 'test-149724~486012', 1, 'SER143'),
              ('program-1497248602', 1497248781, 1497248961, 180, 'test-149724~486022', 2, 'SER143'),
              ('program-1497248603', 1497248961, 1497249141, 180, 'test-149724~486032', 3, 'SER143')]
    """
    final_list = []

    for ser, episodes in series.items():
        for ep in episodes:
            temp_list = []
            contref = ep[0]
            strtTime = iso2epoch(ep[1])
            duration = interval2sec(ep[2])
            endTime = strtTime + duration
            episode_num = ep[3]

            temp_list.append(contref)
            temp_list.append(strtTime)
            temp_list.append(endTime)
            temp_list.append(duration)
            if len(ep) > 3:
                temp_list.append(ep[4])
            temp_list.append(episode_num)
            temp_list.append(ser)

            final_list.append(tuple(temp_list))

    return final_list

def get_contentid_by_scheduleid(cfg, playbackurilist,timeout):
    """
    To get the content id list from recording Id using the RM response
    """
    try:
        if type(playbackurilist) != list:
            playbackurilist = [ playbackurilist ]
            
        recid_list = playbackurilist
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


def stop_recording_inprogress(cfg, plannerid, itemid, timeout=2, pps_host=None):
    """
    Stop a recoding which is in-progress
    :param cfg:
    :param plannerid:
    :return:
    """

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_header(plannerid)
        if headers is None:
            print "Unable to get the booking headers"
            return False

        if not isinstance(itemid, list):
            itemids = [itemid]

        stop_fail = []
        stop_pass = []

        for itemid in itemids:
            payload = dict()
            payload["itemId"] = str(itemid)
            payload = json.dumps(payload)

            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/bookings/stopRecordingInProgress"
            print "Stop the Recording In-progress with url :", url
            print "[INFO: ] Stop Recording Payload ", payload
            print "[INFO: ] Stop Recording Headers ", headers

            r = sendURL("post", url, server_timeout=timeout, header=headers, payload_content=payload)
            print "[INFO: ] Stop Recording Response ", r.content

            if r is not None:
                try:
                    r.raise_for_status()
                    print "PPS V3 - Stop Recording successful"
                    stop_pass.append(itemid)
                except:
                    print "Unable to Stop the Recording %s" % itemid
                    print r.status_code
                    print r.headers
                    stop_fail.append(itemid)
            else:
                print "response is none"
                stop_fail.append(itemid)

        if not stop_fail and len(stop_pass) == len(itemids):
            print "All recordings got Stopped successfully"
            return True
        else:
            print "Following Recordings were not Stopped"
            print stop_fail
            return False

    except Exception as e:
        print "Error in PPS V3 Stop Recording :\n", str(e)
        return False


def diskspace_details(cfg, plannerId, pps_host=None, timeout=2):
    """
    To find Free, total, & used Diskspace for a planner.
    :param cfg:
    :param plannerId:
    :param timeout:
    :return:
    """
    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_booking_header(plannerId)
        if headers is None:
            print "Unable to get the booking headers"
            return False

        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/utils/diskspace"
        print "Fetch the Disk space details with url :", url

        r = sendURL("get", url, server_timeout=timeout, header=headers)

        if r is not None:
            if r.status_code != 200:
                print "Unable to fetch disk space details for the planner %s" % plannerId
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3 - Fetch Disk space is successful"
                return True, r

    except Exception as e:
        print "Error in PPS V3 fetch diskspace:\n", str(e)
        return False

def get_recurrences(cfg, plannerId, timeout=2, pps_host=None):
    """
    Get all the Recurrences of a Planner Id.
    :param cfg: config parameter
    :param plannerId: planner id
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return: (True, response) if success else (False, None)
    """
    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None

        url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recurrences/getRecurrences"
        print "Get Recordings of planner via URL:",url

        r = sendURL("get", url, server_timeout=timeout, header=header)

        if r is not None:
            if r.status_code != 200:
                print "PPS V3 Unable to get the Recurrences via url %s" %url
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3. Got the recurrences of the planner %s"%plannerId
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 get Recurrences :\n", str(e)
        return False, None

def get_recording_series(cfg, plannerId, contentRef, timeout=2, pps_host=None):
    """
    Get the All the Recording of a Planner with the item id
    :param cfg: config parameter
    :param plannerId: planner id
    :param contentRef: content Ref of the recording to get
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return: (True, Response) if success else (False, None)
    """

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        header = get_header(plannerId)
        if header is None:
            print "Unable to get the headers"
            return False, None
        rec_details = None
        res, resp = get_recordings(cfg, plannerId, timeout=timeout)
        if res and resp:
            r = json.loads(resp.content)
            print "Get recordings response:"
            print r
            for i in r['recordings']:
                if i['contentRef'] == contentRef:
                    rec_details = i

        if rec_details:
            return True, rec_details
        else:
            return False, None
    except Exception as e:
        print "Error in PPS V3 get Recording:\n", str(e)
        return False, None

def verify_recording_series(cfg, plannerId, contentRefs, timeout=2, pps_host=None):
    """
        Verify the content is in recording state.
        :param cfg: config parameter
        :param plannerId: planner id
        :param itemids: content Refs to verify
        :param timeout: timeout value
        :param pps_host: pps host <optional>
        :return: True if success else False
        """

    if not isinstance(contentRefs, list):
        contentRefs = [contentRefs]

    recording_pass = []
    recording_fail = []
    for contentRef in contentRefs:
        result, responseDict = get_recording_series(cfg, plannerId, contentRef, timeout=timeout, pps_host=pps_host)

        if result:
            if responseDict["isRecordingComplete"] is False:
                    recording_pass.append(contentRef)
            else:
                    recording_fail.append(contentRef)
        else:
            recording_fail.append(contentRef)

    if not recording_fail and len(recording_pass) == len(contentRefs):
        print "All the itemids are in Recording state"
        return True
    else:
        print "Some itemids are not in recording state: ", recording_fail
        return False

def verify_recorded_series(cfg, plannerId, contentRefs, timeout=2, pps_host=None):
    """
    Verify the content is in recording state.
    :param cfg: config paratmeter
    :param plannerId: planner id
    :param contentRefs: content ref to verify
    :param timeout: timeout value
    :param pps_host: pps host <optional>
    :return: True if success else False
    """

    if not isinstance(contentRefs, list):
        contentRefs = [contentRefs]

    recorded_pass = []
    recorded_fail = []
    for contentRef in contentRefs:
        result, responseDict = get_recording_series(cfg, plannerId, contentRef, timeout=timeout, pps_host=pps_host)

        if result:
            if responseDict["isRecordingComplete"] is False:
                    recorded_pass.append(contentRef)
            else:
                    recorded_pass.append(contentRef)
        else:
            recorded_fail.append(contentRef)
    if not recorded_fail and len(recorded_pass) == len(contentRefs):
        print "All the episodes are in Recorded state"
        return True
    else:
        print "Some episodes are not in recorded state : ", recorded_fail
        return False

def delete_booking_series_event(cfg, plannerId, contentRef, timeout=2, pps_host=None, recurrence=False):
    """
    Delete a Event booking or Series booking based on the payload passed
    :param cfg:
    :param plannerId:
    :param timeout:
    :param printflg:
    :param pps_host:
    :return:
    """

    try:
	itemid = None
	result, responseDict = get_recording_series(cfg, plannerId, contentRef, timeout=timeout, pps_host=pps_host)
	if result:itemid = responseDict["itemId"]
	else:itemid = None
	if itemid:
		print "Successfully got the itemId from the get_recording_series"
	else:
		print "Could not find the itemid within the get_recording_series response "
		return False
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_header(plannerId)
        if headers is None:
            print "Unable to get the Booking headers"
            return False, None

        payload = """{
                      "itemId" : %s
                      }""" % itemid

        print "Headers :",headers
        payload = json.dumps(payload)
        headers = json.dumps(headers)
        if recurrence:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recurrences/deleteRecurrence"
        else:
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/bookings/deleteBooking"

        r = sendURL("post", url, server_timeout=timeout, header=headers, payload_content=payload)
        print "Delete booking via URL :", url

        if r is not None:
            if r.status_code != 204:
                print "PPS V3 Delete_Booking Failed"
                print r.status_code
                print r.headers
                return False, r
            else:
                print "PPS V3 - Delete_Booking successful"
                return True, r
        else:
            return False, None

    except Exception as e:
        print "Error in PPS V3 Delete_booking :\n", str(e)
        return False, None


def get_rec_details_with_xrid(cfg, xrid=None, timeout=6):
    """
    Fetches Recording Details From VMR
    """

    try:
        rec_details_url = cfg['vmr']['url1']
        protocol = rec_details_url['protocol']
        vmr_host = rec_details_url['host']
        vmr_port = rec_details_url['port']
        vmr_uname = rec_details_url['user']
        vmr_pwd = rec_details_url['pwd']
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "Source-Type": "SMS",
            "Source-Id": "123"
        }
        url = protocol + "://" + vmr_host + ":" + str(vmr_port) + "/api/findxrid/" + xrid
        print "URL to get recording details from recording id is :", url
        res = send_vmr_url(
            "get", url, server_timeout=timeout, header=headers,
            auth=(vmr_uname, vmr_pwd))
        if res:
            return True, res
        print "[ERROR: ] Unable to make Fetch Recording Details API call ..."
        return False, None
    except Exception as ex:
        print "[ERROR: ] Unable to make Fetch Recording Details API call due to ", str(ex)
        return False, None


def delete_recording_series(cfg, plannerId, contentRefs, timeout=2, pps_host=None):
    """
    Delete the recording based on the Itemid supplied
    :param cfg: config parameter
    :param plannerId: planner id
    :param contentRef: content Ref of recording to delete
    :param timeout: timeout value
    :param pps_host: pps host(optional)
    :return: True if all the recordings are deleted else False
    """

    itemids = []
    try:
        if not isinstance(contentRefs, list):
            contentRefs = [contentRefs]
        for contentRef in contentRefs:
            result, responseDict = get_recording_series(cfg, plannerId, contentRef, timeout=timeout, pps_host=pps_host)	
            if result:
            	itemids.append(responseDict["itemId"])
            else:
                print "No response from the get_recording_series for the contentRef %s"% contentRef
                return False
    except:
        print "An error occured while collecting the itemId from the get_recordings_series"

    try:
        protocol = cfg['protocol']
        pps_port = cfg['pps']['port']

        if pps_host is None:
            pps_host = cfg['pps']['host']

        headers = get_booking_header(plannerId)
        if headers is None:
            print "Unable to get the booking headers"
            return False

        if not isinstance(itemids, list):
            itemids = [itemids]

        delete_fail = []
        delete_pass = []

        for itemid in itemids:
            payload = dict(itemId=itemid)
            payload = json.dumps(payload)
            url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/recordings/deleteRecording"
            print "Delete the Recording with url: %s\npayload: %s\nheaders: %s" %(url, payload, headers)

            r = sendURL("post", url, server_timeout=timeout, header=headers, payload_content=payload)

            if r is not None:
                if r.status_code != 204: #todo: response would be 200 as per api document
                    print "Unable to Delete the Recording %s"%itemid
                    print r.status_code
                    print r.headers
                    delete_fail.append(itemid)
                else:
                    print "PPS V3 - Delete Recording successful"
                    delete_pass.append(itemid)
            else:
                delete_fail.append(itemid)

        if not delete_fail and len(delete_pass) == len(itemids):
            print "All recordings got Deleted successfully"
            return True
        else:
            print "Following Recordings were not deleted"
            print delete_fail
            return False

    except Exception as e:
        print "Error in PPS V3 Delete Recording:\n", str(e)
        return False

def find_bookings_by_contentref_timerIssue(cfg, plannerId, contentref, timeout=2, pps_host=None):
        """
                Summary:
                        The content in the response were empty when we
                        send a request to get the booking by contentref.
                Issue:
                        There is some timer issue due to which,the
                        bookings are not populated in the booking catalog but the response was 200!.
                Workaround:
                        There are times we are dependent on the response's content.
                        So at those times the this function will be called after
                        waiting for recording delay.
                        The reason for introducing this function separately is that
                        just want to make sure that implementation of the existing TCs
                        are not affected while running.
                Usage:
                        :param cfg: config parameter
                        :param contentref: contentRef of the booked content
                        :param plannerId: planner id
                        :param timeout: timeout value
                        :param pps_host: pps host <optional>
                        :return: (True, Booking response) if success else (False, None)
        """
        try:
                protocol = cfg['protocol']
                pps_port = cfg['pps']['port']

                if pps_host is None:
                        pps_host = cfg['pps']['host']

                header = get_header(plannerId)
                if header is None:
                        print "Unable to get the headers"
                        return False, None

                url = protocol + "://" + pps_host + ":" + str(pps_port) + "/pps/v3/core/findBookingsByContentRef?" \
                                                                          "contentRef=%s" % (contentref)

                r = sendURL("get", url, server_timeout=timeout, header=header)
                print "Find Bookings by contentref via URL : ", url

                if r is not None:
                        #[DEBUG] print "r.content length = ",len(json.loads(r.content)) This debug proves that the booking catalog has some time deley in loading the content
                        if r.status_code != 200 or len(json.loads(r.content)) == 0:
                                print "PPS V3 Unable to find bookings by contentref"
                                print r.status_code
                                print r.headers
                                return False, r
                        else:
                                print "PPS V3 - found the bookings by contentRef"
                                return True, r
		else:
                        return False, None

        except Exception as e:
                print "Error in PPS V3 find Bookings by contentref :\n", str(e)
                return False, None

def switch_authz(cfg, plannerId, choice="ADD",timeout=2, authz_host=None):
        try:
                protocol = cfg['protocol']
                authz_port = cfg['externalAuthz']['port']

                if authz_host is None:
                        authz_host = cfg['externalAuthz']['host']

                header = get_header(plannerId)
                if header is None:
                        print "Unable to get the headers"
                        return False, None

                url = protocol + "://" + authz_host + ":" + str(authz_port) + "/authz/planner/%s"% (plannerId)

                if choice == "ADD":
                        r = sendURL("put", url, server_timeout=timeout, header=header)
                        print "Adding PlanneId to Not Authorized Planner via URL : ", url
                elif choice == "REMOVE":
                        r = sendURL("delete", url, server_timeout=timeout, header=header)
                        print "Removing PlanneId to Not Authorized Planner via URL : ", url

                if r is not None:
                        #[DEBUG] print "r.content length = ",len(json.loads(r.content)) This debug proves that the booking catalog has some time deley in loading the content
                        if r.status_code != 201:
                                print "External Authz unable to process the request."
                                print r.status_code
                                print r.headers
                                return False, r
                        else:
                                print "External Authz successfully able to process the request."
                                return True, r
                else:
                        print "External Authz unable to process the request."
                        return False, None

        except Exception as e:
                print "Error in PPS V3 find Bookings by contentref :\n", str(e)
                return False, None

def debug_print(cfg, planner):
    print "#"*10, " DEBUG STARTED ON PLANNER ", planner, " ", "#"*10

    print "#" * 10, " DEBUG ENDED ON PLANNER ", planner, " ", "#" * 10

def playback_recordedevent_v3(cfg, abspath, test,
                           contentplayuri,recordedtitle,
                           householdid, timeout,
                           printflg,cleanuphousehold=False,
                           iterationcounter=0,
                           recordedcontentduration=None
                          ):
    pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }                          
    pps_host = [cfg['pps']['host']]
    pps_port = cfg['pps']['port']      

    prmsupportedflag = cfg['prm_supported']
    proxyhostcheckflag = cfg['proxyHostNeeded']
    proxy_host = cfg['proxyhost']['host']
    proxy_port = cfg['proxyhost']['port']
    contentplayback_host = cfg['contentplayback']['host']
    contentplayback_port = cfg['contentplayback']['port']
    contentplayback_url = cfg['contentplayback']['url']
    rm_host = cfg['rm']['host']
    protocol = cfg['protocol']

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
                    cleanup_planner(cfg, householdid)
                    return ("FAIL",message)

            #Do the RM CNS API call instead of PRM to get the content ID
            else:
                #Get the ContentID from RM CNS API
                # REMOVE THIS
                #1 contentId = get_contentID_withoutPRM(protocol,rm_host,contentplayuri,timeout,pps_headers,printflg)
                contentId = get_contentid_by_scheduleid(cfg, contentplayuri, timeout)
                if contentId:
                    contentId = type(contentId) == list and contentId[0] or contentId
                    #Get the Content URL using contentID
                    if proxyhostcheckflag == True:
                        contentURL = get_contentURL_withoutPRM(protocol,proxy_host,proxy_port,contentplayback_url,contentId,printflg)
                    else:
                        contentURL = get_contentURL_withoutPRM(protocol,contentplayback_host,contentplayback_port,contentplayback_url,contentId,printflg)
                else:
                    message = "Testcase Failed: Unable to Fetch contentid for the playback"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_planner(cfg, householdid)
                    return ("FAIL",message)

            #Download the manifest file for that response
            if contentURL:
                print "Download the manifest file via" + contentURL
                manifestfileresponse = sendURL('get',contentURL,timeout,pps_headers)
                if manifestfileresponse is not None:
                    if manifestfileresponse.status_code == 200:
                        if manifestfileresponse.content == "":
                            message = "Testcase Failed: Manifestfile Response is empty"
                            cleanup_planner(cfg, householdid)
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
                                cleanup_planner(cfg, householdid)
                                return ("FAIL",message)
                            downloadfileresponse = sendURL('get',videoplaybackurl,20,pps_headers)
                            if downloadfileresponse is not None:
                                if downloadfileresponse.status_code == 200:
                                    if downloadfileresponse.content == "":
                                        message = "Testcase Failed: Download file response is empty"
                                        cleanup_planner(cfg, householdid)
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
                                    cleanup_planner(cfg, householdid)
                                    return ("FAIL",message) 
                            else:
                                message = "Testcase Failed: Unable to fetch downloadfileresponse"
                                cleanup_planner(cfg, householdid)
                                return ("FAIL",message)
                    else:
                        message = "Testcase Failed: Unable to fetch Manifest File contents"
                        print manifestfileresponse.status_code
                        print manifestfileresponse.content
                        cleanup_planner(cfg, householdid)
                        return ("FAIL",message)
                else:
                    message = "Testcase Failed: Unable to fetch Manifest file"
                    cleanup_planner(cfg, householdid)
                    return ("FAIL",message)
            else:
                message = "Testcase Failed: Unable to fetch ContentURL"
                cleanup_planner(cfg, householdid)
                return ("FAIL",message)

            #Teardown the SM Session
            if prmsupportedflag == True and smsessionid != None and statinfo.st_size:
                sm_host = cfg['sm']['host']
                if teardownsmsession(protocol,sm_host,sm_port,smsessionid,printflg):
                    message = "Testcase Passed: SM Session deleted successfully and cleaned up successfully"
                    if cleanuphousehold:
                        cleanup_planner(cfg, householdid)
                    return ("PASS",message)
                else:
                    message = "Testcase Failed: Unable to delete SM Session"
                    cleanup_planner(cfg, householdid)
                    return ("FAIL",message)
            elif prmsupportedflag == False and statinfo.st_size:
                message = "Testcase Passed: Event recorded and Played back successfully"
                if cleanuphousehold:
                    cleanup_planner(cfg, householdid)
                return ("PASS",message)
            else:
                message = "Testcase Failed: Unable to get the sessionid or size of the video file"
                cleanup_planner(cfg, householdid)
                return ("FAIL",message)
        except:
            message = "Testcase Failed: Error Occurred in Playback Session: " + PrintException(True)
            cleanup_planner(cfg, householdid)
            return ("FAIL",message)
    else:
        message = "Testcase Failed: Unable to fetch contentplayuri or recordedtitle for playback"
        cleanup_planner(cfg, householdid)
        return ("FAIL",message)


def verify_common_unique_copy_type(cfg, plannerid_list, itemId_list, timeout, fanout=0, verifyfanout=True,common_copy=True):
    """
    Verify the recording is a commnon copy.
    If the same even in a channel is recorded from multiple households and if the even is common copy then only one recording will be done
    and shared by all the households.
    For that common recording the fanout value will be <Number of households-1>
    :param cfg: configuration variable
    :param plannerid_list: List of household ids
    :param itemId_list: List of content ids used for pps boooking
    :param timeout: timeout value
    :param fanout: Maximum fanout value <No of Households - 1>
    :param verifyfanout: Optional - If True the Fanout value will be verified. If False the fanout value will not be verified the calling function
                        should take care of it
    :return:If the fanout value verification is success list of content ids will be returned else False
    """

    try:
        content_playback_list = get_content_playBackUri(cfg, itemId_list, plannerid_list, timeout=timeout)
        assert content_playback_list, "Testcase Failed : Unable to retrieve contentplaybackURI"
        assert len(content_playback_list) == len(
            plannerid_list), "Testcase Failed: Unable to get the contentplayuri for all the planner ids"
        print "Content playback URI:", content_playback_list
        content_id_list = get_contentid_by_scheduleid(cfg, content_playback_list, timeout)
        assert content_id_list, "Testcase Failed : Unable to retrieve recording ID"
        print "Content Id List:", content_id_list
        streamidstartendtime_list = get_start_and_end_time(cfg, content_id_list, timeout)
        assert streamidstartendtime_list, "Testcase Failed : Unable to retrieve contentID"
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
        if ((len(start_time[0]) == len(plannerid_list)) and (len(end_time[0]) == len(plannerid_list)) and (
            len(streamid[0]) == len(plannerid_list))):
            main_list.append(start_time[0][0])
            main_list.append(end_time[0][0])
        else:
            message = "Length of Starttime or Endtime list is not same as the plannerids"
            return False, message
        streamid = streamid[0][0]
        isid = isid_list[0][0]
        batchid = batchid_list[0][0]
        print "StreamId : {0} ISIS : {1} BatchID : {2}".format(streamid, isid, batchid)
        segmentIdList = get_segment_response(cfg, main_list, streamid, timeout)
        assert segmentIdList, "Unable to retrieve segment values"

        if verifyfanout:
            if verify_FanOut_value(cfg, segmentIdList, isid, timeout, batchid, 0, True):
                message = "CommonCopy Success -> Fanout value is : ", fanout, " for the conetentId :", content_id_list
                return True, message
            else:
                message = "Fanout value is not as expected"
                return False, message
        else:
            return True, segmentIdList
    except Exception as e:
        return False, str(e)

def playback_and_stop_recording_event_v3(cfg, abspath, test,
                           contentplayuri,recordedtitle,
                           householdid, timeout,
                           printflg,cleanuphousehold=False,
                           iterationcounter=0,
                           recordedcontentduration=None
                          ):
    pps_headers = {
            'Content-Type': 'application/json',
            'Source-Type': 'WEB',
            'Source-ID': '127.0.0.1',
            }
    pps_hosts = [cfg['pps']['host']]
    pps_port = cfg['pps']['port']

    prmsupportedflag = cfg['prm_supported']
    proxyhostcheckflag = cfg['proxyHostNeeded']
    proxy_host = cfg['proxyhost']['host']
    proxy_port = cfg['proxyhost']['port']
    contentplayback_host = cfg['contentplayback']['host']
    contentplayback_port = cfg['contentplayback']['port']
    contentplayback_url = cfg['contentplayback']['url']
    rm_host = cfg['rm']['host']
    protocol = cfg['protocol']
    # Changed to a traditional config instead of the new config
    recordedStateChange = cfg['pps']['recording_to_recorded_delay']

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
                    cleanup_planner(cfg, householdid)
                    return ("FAIL",message)

            #Do the RM CNS API call instead of PRM to get the content ID
            else:
                #Get the ContentID from RM CNS API
                # REMOVE THIS
                #1 contentId = get_contentID_withoutPRM(protocol,rm_host,contentplayuri,timeout,pps_headers,printflg)
                contentId = get_contentid_by_scheduleid(cfg, contentplayuri, timeout)
                if contentId:
                    contentId = type(contentId) == list and contentId[0] or contentId
                    #Get the Content URL using contentID
                    if proxyhostcheckflag == True:
                        contentURL = get_contentURL_withoutPRM(protocol,proxy_host,proxy_port,contentplayback_url,contentId,printflg)
                    else:
                        contentURL = get_contentURL_withoutPRM(protocol,contentplayback_host,contentplayback_port,contentplayback_url,contentId,printflg)
                else:
                    message = "Testcase Failed: Unable to Fetch contentid for the playback"
                    debug_print_log(pps_port,protocol,pps_host,householdid,timeout)
                    cleanup_planner(cfg, householdid)
                    return ("FAIL",message)

            #Download the manifest file for that response
            if contentURL:
                print "Download the manifest file via" + contentURL
                manifestfileresponse = sendURL('get',contentURL,timeout,pps_headers)
                if manifestfileresponse is not None:
                    if manifestfileresponse.status_code == 200:
                        if manifestfileresponse.content == "":
                            message = "Testcase Failed: Manifestfile Response is empty"
                            cleanup_planner(cfg, householdid)
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
                                cleanup_planner(cfg, householdid)
                                return ("FAIL",message)
                            downloadfileresponse = sendURL('get',videoplaybackurl,20,pps_headers)
                            if downloadfileresponse is not None:
                                if downloadfileresponse.status_code == 200:
                                    if downloadfileresponse.content == "":
                                        message = "Testcase Failed: Download file response is empty"
                                        cleanup_planner(cfg, householdid)
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
                                                    print "Playback has started properly from where it started recording."
                                                
                                                    print "Video Sample saved in the same folder with the name " + downloadfile + " with the size of " + str(statinfo.st_size) + " bytes"
                                                    print "Now the playback is going to be stopped.\n\n"
                                                    #Stopping the Recording when the Recording is in progress and playback
                                                    stop_recording = stoprecording(protocol, pps_host, pps_port, contentplayuri, timeout)
                                                    if stop_recording == "PASS":
                                                        print "Recording is successfully cancelled(stopped) during Recording and Playback.\nWaiting for some time to move the content to recorded catalog."
                                                        time.sleep(recordedStateChange)
                                                        print "Playback stopped successfully and the content will be moved to recorded library."
                                                        #rec_rslt,rec_resp = verify_recorded_state(pps_port, protocol, pps_host, householdid,event_contentId, timeout)
                                                        #if rec_rslt == "PASS":
                                                        #    message = "Event is successfully stopped and in recorded library"
                                                        #    return ("PASS",message)
                                                        #else:
                                                        #    message = "Testcase Failed, Event is not present in the recorded catalog"
                                                        #    return ("FAIL",message)
                                                    else:
                                                        message = "Error in stopping the recording"
                                                        return ("FAIL",message)
                                                else:
                                                    message = "Testcase Failed: Playback started and ended does not match to the Recording Start and End point"
                                                    return ("FAIL",message)
                                            else:
                                                pass
                                else:
                                    message = "Testcase Failed: Unable to fetch downloadfileresponse contents"
                                    print downloadfileresponse.status_code
                                    print downloadfileresponse.content
                                    cleanup_planner(cfg, householdid)
                                    return ("FAIL",message)
                            else:
                                message = "Testcase Failed: Unable to fetch downloadfileresponse"
                                cleanup_planner(cfg, householdid)
                                return ("FAIL",message)
                    else:
                        message = "Testcase Failed: Unable to fetch Manifest File contents"
                        print manifestfileresponse.status_code
                        print manifestfileresponse.content
                        cleanup_planner(cfg, householdid)
                        return ("FAIL",message)
                else:
                    message = "Testcase Failed: Unable to fetch Manifest file"
                    cleanup_planner(cfg, householdid)
                    return ("FAIL",message)
            else:
                message = "Testcase Failed: Unable to fetch ContentURL"
                cleanup_planner(cfg, householdid)
                return ("FAIL",message)

            #Teardown the SM Session
            if prmsupportedflag == True and smsessionid != None and statinfo.st_size:
                sm_host = cfg['sm']['host']
                if teardownsmsession(protocol,sm_host,sm_port,smsessionid,printflg):
                    message = "Testcase Passed: SM Session deleted successfully and cleaned up successfully"
                    if cleanuphousehold:
                        cleanup_planner(cfg, householdid)
                    return ("PASS",message)
                else:
                    message = "Testcase Failed: Unable to delete SM Session"
                    cleanup_planner(cfg, householdid)
                    return ("FAIL",message)
            elif prmsupportedflag == False and statinfo.st_size:
                message = "Testcase Passed: Event recorded and Played back successfully"
                if cleanuphousehold:
                    cleanup_planner(cfg, householdid)
                return ("PASS",message)
            else:
                message = "Testcase Failed: Unable to get the sessionid or size of the video file"
                cleanup_planner(cfg, householdid)
                return ("FAIL",message)
        except:
            message = "Testcase Failed: Error Occurred in Playback Session: " + PrintException(True)
            cleanup_planner(cfg, householdid)
            return ("FAIL",message)
    else:
        message = "Testcase Failed: Unable to fetch contentplayuri or recordedtitle for playback"
        cleanup_planner(cfg, householdid)
        return ("FAIL",message)


def get_recording_state_change_time(start_time):
    """
    To get the time taken for recording state change
    :param start_time: start time of the program
    :return: wait time
    """
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    wait_time = (start_time - datetime.datetime.utcnow()).total_seconds()
    if wait_time > -10:
        wait_time += 20
    else:
        wait_time = 0
    return wait_time


def get_recorded_state_change_time(start_time, program_length):
    """
    To get the time taken for recorded state change
    :param start_time: start time of the program
    :param program_length: duration of the program
    :return: wait time
    """
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    end_time = start_time + datetime.timedelta(minutes=program_length)
    wait_time = (end_time - datetime.datetime.utcnow()).total_seconds()
    if wait_time > -10:
        wait_time += 20
    else:
        wait_time = 0
    return wait_time


if __name__ =="__main__":
    '''print get_booking_header("keya2")
    plannerId = "keya1"

    cfg={}
    cfg['pps'] = {'host': "10.78.221.239",'port': "6060"}
    cfg['seriesResolution'] = {'host':"10.78.221.239",'port': "6060"}
    cfg['protocol'] = "http"

    payload = """{
                            "eventChannel": "123",
                            "eventStartTime": "2017-01-19T13:55:00Z",
                            "eventDurationInSeconds": "3000",
                            "metadataContentRef":"program-404387-514850",
                            "recurrence":"series"}"""

    ret, resp = create_booking(cfg, plannerId, payload, timeout=2, printflg=False, pps_host="10.78.221.239")
    print "#### Response ####\n"
    print resp.headers
    print "\n##################"

    ev = [('program-1497248599', '2017-06-12T06:26:19Z', 'PT00H05M00S', 'program-149724~485992'),
          ('program-1497248600', '2017-06-12T06:31:19Z', 'PT00H05M00S', 'program-149724~486002')]
    sr = sr = {'SER143': [('program-1497248601', '2017-06-12T06:23:21Z', 'PT00H03M00S', 1, 'test-149724~486012'),
                          ('program-1497248602', '2017-06-12T06:26:21Z', 'PT00H03M00S', 2, 'test-149724~486022'),
                          ('program-1497248603', '2017-06-12T06:29:21Z', 'PT00H03M00S', 3, 'test-149724~486032')]}
    print get_contentref_details(ev)
    print get_contentref_details_series(sr)'''



    print interval2sec("PT00H15M25S")
    print sec2interval(925)
