"""
All the Helper function related to PPS V3 planner are here.
"""

import time
from L1commonFunctions import *



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


def get_booking_header(plannerId):
    try:
        planner = "{\"hhId\":\"%s\"}" % plannerId
        header = {
                "x-cisco-vcs-identity": planner,
                "Content-Type": "application/json"
                }
        return header
    except Exception as e:
        print "Error in get booking headers :\n",str(e)
        return None


def get_header(plannerId):
    planner = "{\"hhId\":\"%s\"}" % plannerId
    header = {
                 "x-cisco-vcs-identity": planner
             }
    return header


def create_planner(cfg, plannerId, allowRecording=True, region=None, recorderRegion=None, numOfTuners=None, diskQuota=None, userAuthorizationToken=None, timeout=10):
    """
    Create Planner for pps
    :param cfg: configuration parameter
    :param plannerId: planner name
    :param allowRecording: <optional> argument to decide whether the planner is authorised ofr booking
    :param timeout: <optional> max timeout value
    :param region: <optional> region number
    :param recorderRegion: <optional> recorder region
    :param numOfTuners: <optional> number of tuners
    :param diskQuota: <optional> default disk quota for a planner
    :return: Retuen TRUE on success FALSE on failure
    """

    # set values based on config
    protocol = cfg['protocol']
    host = cfg['pps']['host']
    port = cfg['pps']['port']

    if allowRecording:
        allowrecording = "true"
    else:
        allowrecording = "false"

    if not region:
        region = cfg['planner']['channelMapRegion']
    if not recorderRegion:
        recorderRegion = cfg['planner']['recorderRegion']
    if not numOfTuners:
        numOfTuners = cfg['planner']['numOfTuners']
    if not diskQuota:
        diskQuota = cfg['planner']['diskQuota']

    if not userAuthorizationToken:
        userAuthorizationToken = cfg['planner']['userAuthorizationToken']

    #headers = get_header(plannerId)
    headers = {
                'Content-Type':'application/json'
                }
    payload = """
        {
          "plannerId" : "%s",
          "allowRecording" : %s,
          "recorderRegion" : "%s",
          "channelMapRegion": "%s",
          "numOfTuners" : %d,
          "diskQuota" :"%s",
          "userAuthorizationToken":"%s"
          }
        """ % (plannerId, allowrecording, recorderRegion, region, numOfTuners, diskQuota,  userAuthorizationToken)

    #print payload
    #print headers

    url = protocol + "://" + host + ":" + str(port) + "/pps/provisioning/v1/planners/createPlanner"

    if planner_exists(cfg, plannerId):
        print "Planner already present : ", plannerId
        return True
    else:
        try:
            print "Create household via " + url

            r = sendURL("post", url, payload_content=payload, header=headers, server_timeout=timeout)
            #print r
            if r is None:
               return False
            if r.status_code != 200:
                print r.status_code
                print r.headers
                print r.content
                return False
            else:
                return True
        except Exception as e:
            print "Error: ", str(e)
            return False


def update_planner(cfg, plannerId, allowRecording=None, region=None, recorderRegion=None, numOfTuners=None, diskQuota=None, userAuthorizationToken=None, timeout=10):
    """
    Update the planner
    :param cfg:
    :param plannerId:
    :param timeout:
    :param region:
    :param recorderRegion:
    :param numOfTuners:
    :param diskQuota:
    :return:
    """

    try:
        # set values based on config
        protocol = cfg['protocol']
        host = cfg['pps']['host']
        port = cfg['pps']['port']

        pl = {"plannerId": plannerId}

        if allowRecording:
            pl["allowRecording"] = "%s" %allowRecording

        if region:
            pl["channelMapRegion"] = region

        if recorderRegion:
            pl["recorderRegion"] = recorderRegion

        if numOfTuners:
            pl["numOfTuners"] = numOfTuners

        if diskQuota:
            if not str(diskQuota).startswith("PT"):
                diskQuota = sec2interval(int(diskQuota))
            pl["diskQuota"] = diskQuota

        if userAuthorizationToken:
            pl["userAuthorizationToken"] = userAuthorizationToken

        pay = ""
        count = 1
        for k, v in pl.items():
            pay = pay + '"%s":"%s"' % (k, v)
            if count < len(pl):
                pay = pay + ", "
            count += 1

        payload = """{%s}""" % pay

        #headers = get_header(plannerId)
        headers = {
            'Content-Type': 'application/json'
        }


        print "Payload:\n", payload

        url = protocol + "://" + host + ":" + str(port) + "/pps/provisioning/v1/planners/updatePlanner"

        print "Update Planner via " + url

        r = sendURL("post", url, payload_content=payload, header=headers, server_timeout=timeout)
        if r is None:
            return False
        if r.status_code != 200:
            print r.status_code
            print r.headers
            print r.content
            return False
        else:
            return True
    except Exception as e:
        print "Error in update_planner: ", str(e)
        return False


def get_planner(cfg, plannerid, timeout=10):
    """
    Fetch all the details of an existing plannerID
    :param cfg:
    :param plannerid:
    :param timeout:
    :return:
    """
    try:
        protocol = cfg['protocol']
        port = cfg['pps']['port']
        pps_host = cfg['pps']['host']

        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/provisioning/v1/planners/getPlanner?plannerId=%s"% plannerid
        print "\nGet Planner with URL : ", url
        r = sendURL("get", url, server_timeout=timeout)
        if r.status_code == 200:
            return True, r
        else:
            return False, r

    except Exception as e:
        print "Exception in get_planner."
        print str(e)
        return False, None


def delete_planner(cfg, plannerId, timeout=10):
    """
    This Function will delete an household if it exists.
    :param cfg:
    :param plannerId:
    :param timeout:
    :return Boolean
    """

    protocol = cfg['protocol']
    port = cfg['pps']['port']
    pps_host = cfg['pps']['host']

    payload = '{"plannerId":"%s"}' % plannerId

    headers = {
        'Content-Type': 'application/json'
    }

    #print payload

    try:

        url = protocol + "://" + pps_host + ":" + str(port) + "/pps/provisioning/v1/planners/deletePlanner"
        print "\nDelete Planner %s Via URL : %s" %(plannerId, url)
        r = sendURL("post", url, payload_content=payload, server_timeout=timeout, header=headers)
        if r is None:
            print "Unable to delete the Planner %s" %plannerId
            return False
        if r.status_code != 200:
            if r.status_code == 404 and "resource does not exist" in r.content:
                print "Planner %s not present" %plannerId
                return True
            print r.status_code
            print r.content
            return False
        return True

    except Exception as e:
        print str(e)
        return False


def planner_exists(cfg, plannerId, timeout=10):
    try:
        res, resp = get_planner(cfg, plannerId, timeout)
        if res:
            #print "Planner %s exist" % plannerId
            return True
        else:
            #print "Planner %s doesn't exist"%plannerId
            return False
    except:
        print "Error in verifying the Planner Exist."
        return False


def get_planner_diskquota(cfg, planner, timeout=10):
    """
    Get the diskquota of the planner specified
    :param cfg:
    :param planner:
    :param timeout:
    :param pps_host:
    :return:
    """
    result, response = get_planner(cfg, planner, timeout)
    if result:
        planner_content = json.loads(response.content)
        old_diskquota = planner_content['diskQuota']
        return old_diskquota
    else:
        print "Unable to Fetch Planner details"
        return False


def get_planner_tunerquota(cfg, planner, timeout=10):
    """
    Get the tuner quota of the planner specified
    :param cfg:
    :param planner:
    :param timeout:
    :param pps_host:
    :return:
    """
    result, response = get_planner(cfg, planner, timeout)
    if result:
        planner_content = json.loads(response.content)
        tunerquota = planner_content['numOfTuners']
        return str(tunerquota)
    else:
        print "Unable to Fetch Planner details"
        return False


def cleanup_planner(cfg, planner, timeout=10):
    print "#" * 10, " CLEANUP STARTED ON PLANNER ", planner, " ", "#" * 10
    # Reset TunerQuota
    # Reset DiskQuota
    # Enable allowRecording
    # Delete Bookings
    # Delete Recordings
    # Delete Recorded contents
    delete_planner(cfg, planner)
    res = create_planner(cfg, planner)
    print "#" * 10, " CLEANUP ENDED ON PLANNER ", planner, " ", "#" * 10
    return res


def create_plnr(cfg, plannerId, allowRecording=True, region=None, recorderRegion=None, numOfTuners=None, diskQuota=None, userAuthorizationToken=None, timeout=10, is_custom_rr=False):
    """
    Create Planner for pps
    :param cfg: configuration parameter
    :param plannerId: planner name
    :param allowRecording: <optional> argument to decide whether the planner is authorised ofr booking
    :param timeout: <optional> max timeout value
    :param region: <optional> region number
    :param recorderRegion: <optional> recorder region
    :param numOfTuners: <optional> number of tuners
    :param diskQuota: <optional> default disk quota for a planner
    :return: Retuen TRUE on success FALSE on failure
    """

    # set values based on config
    protocol = cfg['protocol']
    host = cfg['pps']['host']
    port = cfg['pps']['port']

    if allowRecording:
        allowrecording = "true"
    else:
        allowrecording = "false"

    if not region:
        region = cfg['planner']['channelMapRegion']
    if not is_custom_rr and not recorderRegion:
        recorderRegion = cfg['planner']['recorderRegion']
    if not numOfTuners:
        numOfTuners = cfg['planner']['numOfTuners']
    if not diskQuota:
        diskQuota = cfg['planner']['diskQuota']

    if not userAuthorizationToken:
        userAuthorizationToken = cfg['planner']['userAuthorizationToken']

    #headers = get_header(plannerId)
    headers = {
                'Content-Type':'application/json'
                }
    payload = """
        {
          "plannerId" : "%s",
          "allowRecording" : %s,
          "recorderRegion" : "%s",
          "channelMapRegion": "%s",
          "numOfTuners" : %d,
          "diskQuota" :"%s",
          "userAuthorizationToken":"%s"
          }
        """ % (plannerId, allowrecording, recorderRegion, region, numOfTuners, diskQuota,  userAuthorizationToken)

    #print payload
    #print headers

    url = protocol + "://" + host + ":" + str(port) + "/pps/provisioning/v1/planners/createPlanner"

    if planner_exists(cfg, plannerId):
        print "Planner already present : ", plannerId
        return True
    else:
        try:
            print "Create household via " + url

            r = sendURL("post", url, payload_content=payload, header=headers, server_timeout=timeout)
            #print r
            if r is None:
               return False, r
            if r.status_code != 200:
                print r.status_code
                print r.headers
                print r.content
                return False, r
            else:
                return True, r
        except Exception as e:
            print "Error: ", str(e)
            return False, r
