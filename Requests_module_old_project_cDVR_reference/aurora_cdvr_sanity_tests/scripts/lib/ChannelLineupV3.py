"""
This module will generate the XML file in Canonical Format suitable for PPSv3.

- Based on the Input from the user the Event / Series or both will will be added to the XML.
- Create a corresponding Ingest.json and manifest.json file
- Newly created xml file and ingest.json and manifest.json file will pushed into the SFTP folder specified
- Finally by default the XML file will be removed from the directory <it can be overridden to keep the file>

Using this Module:
    ch = ChannelLineupV3()
    print ch.add_event(start_time_delay_mins=3, duration_min=3, service_id=59684, num_of_events=3)

    print ch.add_series(serviceId=1049, timeSlotLengthMinutes=2, episodeCount=2)

    All Other Options for Series Ingest
    # print ch.add_series(serviceId=55443, timeSlotLengthMinutes=2, episodeCount=5, programIDPrefix="test", gap_mins=5, startepisodenumber=1,
    #                    rebroadcast=[3,5], rebroadcastdealy_mins=10, starttimedelay_mins=15)

"""

# Developed based on pps-schedule.xsd

# ToDo
# 1) Move the default values to config file
# 2) Include a timestamp after the .tar file

import os
import time
import datetime
import calendar
import random
import xml.etree.ElementTree as ET
import paramiko
import json
import sys
import boto3

class ChannelLineupV3(object):
    def __init__(self):
        self.default_duration = 5

        # ################## S3SFTP Server Details #####################
        self.sftp_host = "10.78.217.22"
        self.sftp_port = 22
        self.sftp_user = "root"
        self.sftp_password = "generic@123"
        self.ingest_location = "/home/gningest/"
        self.final_xml = "channel_ingest_"+str(time.strftime("%Y%m%d%H%M%S", time.gmtime(time.time())))+".xml"
        self.ingest_json = "ingest.json"
        self.manifest_json = "manifest-can.json"
        self.file_to_push = [self.final_xml, self.ingest_json, self.manifest_json]
        self.bucket = "cdvr-metadata-ingest"
        ###############################################################

        self.tree = ET.Element("root")
        self.tree.attrib['version'] = "1.0"
        self.sch = None
        self.event = None
        self.contents = None
        self.channel = None
        self.parental_ratings = ("TV-G", "TV-PG", "TV-14", "TV-Y", "TV-Y7", "TV-MA")
        self.startTimeEpoch = []
        self.endTimeEpoch = []
        self.start_time = 0
        self.end_time = {}

    def add_event(self, start_time_delay_mins=0, duration_min=5, service_id=1234, num_of_events=12, gap_mins=0, event_id_prefix="program"):
        """
        Function to add event
        :param start_time_delay_mins: start time delay in minutes <optional>
        :param duration_min: duration of the event
        :param service_id: Service id or channel id in which the event is ingested
        :param num_of_events: number of event to ingest
        :param gap_mins : gap in between events in minutes
        :return: list of event details in the format [(contentRef, starttime, duration, eventId)]
        """

        ret = []

        if service_id not in self.end_time.keys():
            self.end_time[service_id] = 0

        # Calculate the Start time
        if self.end_time[service_id]:
            self.start_time = (start_time_delay_mins * 60) + self.end_time[service_id]
        else:
            self.start_time = time.time() + (start_time_delay_mins * 60)
        _start_time = self.epoch2iso(self.start_time)

        # Calculate the End time
        self.end_time[service_id] = self.start_time + (duration_min * 60 * num_of_events) + (gap_mins * (num_of_events -1) * 60)
        _end_time = self.epoch2iso(self.end_time[service_id])

        self.startTimeEpoch.append(self.start_time)
        self.endTimeEpoch.append(self.end_time[service_id])

        # Convert Duration to the new format
        duration = self.convert_duration(duration_min)


        self.sch = ET.SubElement(self.tree, "schedule")
        self.sch.attrib['startTime'] = _start_time
        self.sch.attrib['endTime'] = _end_time

        # Schedule -> Channel
        self.chn = ET.SubElement(self.sch, "channel")
        self.chn.attrib['channelId'] = str(service_id)

        # Create n number of events based on the num_of_events
        for n in range(0, num_of_events):
            _eve_start_time = self.start_time + (n * duration_min * 60) + (n * gap_mins * 60)
            eve_start_time = self.epoch2iso(_eve_start_time)

            self.event = ET.SubElement(self.chn, "event")
            self.event.attrib['startTime'] = eve_start_time
            self.event.attrib['duration'] = str(duration)
            cont_ref = self.get_program_id(event_id_prefix)
            self.event.attrib['contentRef'] = cont_ref
            event_id = self.get_event_id(title=event_id_prefix)
            self.event.attrib['eventId'] = event_id
            self.event.attrib['parentalRating'] = "TV-G"
            temp_ret = (cont_ref, eve_start_time, duration, event_id)
            ret.append(temp_ret)
            time.sleep(0.05)

        return ret

    def add_series(self, service_id, duration_min=2, episode_count=2, event_id_prefix="program", gap_mins=0, startepisodenumber=1, rebroadcast=[],
                   rebroadcastdealy_mins=0, start_time_delay_mins=0, parental_rating="TV-G", seriesMaster=True, series_id=None):
        """
        Function to add series based on the inputs.
        :param service_id: channel in which the series needs to be ingested
        :param duration_min: length of the episode
        :param episode_count: number of episode
        :param event_id_prefix: prefix that should be added in the event id
        :param gap_mins: time gap in between the eiposods in minutes
        :param startepisodenumber: starting episode number
        :param rebroadcast: episode that needs to be rebroadcasted
        :param rebroadcastdealy_mins: time delay before rebroadcast
        :param start_time_delay_mins: intial time delay in minutes
        :param parental_rating: parental rating of the episode
        :return: dictionary of { series id : [content ref , starttime, duration, episode number, event id]}
        """

        ret = {}
        tempStartEpisodeNumber = startepisodenumber

        if service_id not in self.end_time.keys():
            self.end_time[service_id] = 0

        # Calculate the Start time
        if self.end_time[service_id]:
            self.start_time = (start_time_delay_mins * 60) + self.end_time[service_id]
        else:
            self.start_time = time.time() + (start_time_delay_mins * 60)

        _start_time = self.epoch2iso(self.start_time)

        # Calculate the End time
        self.end_time[service_id] = self.start_time + duration_min * (episode_count + len(rebroadcast)) * 60 + rebroadcastdealy_mins * 60 + ((episode_count -1)* gap_mins *60)
        if len(rebroadcast) > 1:
            self.end_time[service_id] += ((len(rebroadcast) - 1) * gap_mins * 60)
        _end_time = self.epoch2iso(self.end_time[service_id])

        self.startTimeEpoch.append(self.start_time)
        self.endTimeEpoch.append(self.end_time[service_id])

        # Convert Duration to the new format
        duration = self.convert_duration(duration_min)

        # Generate the SeriesID and SeasonID
        if series_id:
            self.series_id = series_id
        else:
            self.series_id = self.generate_series_id()
            
        self.season_id = self.generate_season_id()

        ret.setdefault(self.series_id, [])

        # Root -> Schedule
        #if ET.Element.find(self.tree, "schedule") is None:
        if self.tree.find("schedule") is None:
            self.sch = ET.SubElement(self.tree, "schedule")
        self.sch.attrib['startTime'] = _start_time
        self.sch.attrib['endTime'] = _end_time

        # Schedule -> Channel
        self.channel = ET.SubElement(self.sch, "channel")
        self.channel.attrib['channelId'] = str(service_id)

        # Root -> Contents
        #print "Subelements :", ET.Element.find(self.tree, "contents")
        #if ET.Element.find(self.tree, "contents") is None:
        if self.tree.find("contents") is None:
            self.contents = ET.SubElement(self.tree, "contents")

        # Root -> Channels
        # if ET.Element.find(self.tree, "channels") is None:
        if self.tree.find("channels") is None:
            self.channels = ET.SubElement(self.tree, "channels")

        # Verify Parental Rating
        if parental_rating not in self.parental_ratings:
            print "Parental rating mention is not valid, setting it to TV-G"
            parental_rating = "TV-G"

        # Schedule -> Channel -> Event
        for n in range(0, episode_count):
            _eve_start_time = self.start_time + (n * duration_min * 60) + (n * gap_mins * 60)
            eve_start_time = self.epoch2iso(_eve_start_time)

            self.event = ET.SubElement(self.channel, "event")

            self.event.attrib['startTime'] = eve_start_time
            self.event.attrib['duration'] = str(duration)
            cont_ref = self.get_program_id(event_id_prefix)
            self.event.attrib['contentRef'] = cont_ref
            event_id = self.get_event_id(title=event_id_prefix)
            self.event.attrib['eventId'] = event_id
            self.event.attrib['parentalRating'] = parental_rating
            self._add_content(cont_ref, seriesMaster)

            temp_ret = (cont_ref, eve_start_time, duration, startepisodenumber, event_id)
            startepisodenumber += 1
            time.sleep(0.05)
            ret[self.series_id].append(temp_ret)

        temp_rebroadcastdelay = rebroadcastdealy_mins
        _eve_start_time += (duration_min * 60)
        for count, re_rp in enumerate(rebroadcast):
            episodes = ret.values()[0]
            # print "Episodes :", episodes

            ep = re_rp - tempStartEpisodeNumber
            print "Rebroadcasting episode ", re_rp
            # self.iso2epoch(episodes[ep][1]) + (re_rp * timeSlotLengthMinutes * 60) +
            _eve_start_time = _eve_start_time + (temp_rebroadcastdelay * 60) + (count * duration_min * 60) + (count * gap_mins *60)
            temp_rebroadcastdelay = 0
            eve_start_time = self.epoch2iso(_eve_start_time)

            self.event = ET.SubElement(self.channel, "event")

            self.event.attrib['startTime'] = eve_start_time
            self.event.attrib['duration'] = episodes[ep][2]
            self.event.attrib['contentRef'] = episodes[ep][0]
            self.event.attrib['eventId'] = self.get_event_id(title=event_id_prefix)
            self.event.attrib['parentalRating'] = parental_rating
            self._add_content(episodes[ep][0], seriesMaster)

            temp_ret = (episodes[ep][0], episodes[ep][1], episodes[ep][2], re_rp)
            time.sleep(0.05)
            ret[self.series_id].append(temp_ret)

        self.add_chan_details(service_id)
        return ret

    def _add_content(self, cont_ref, seriesMaster=False):
        self.content = ET.SubElement(self.contents, "content")
        self.content.attrib['contentId'] = cont_ref
        if seriesMaster:
            self.content.attrib['seriesMaster'] = "true"

        self.cont_grp_season = ET.SubElement(self.content, "group")
        self.cont_grp_season.attrib['groupId'] = self.season_id
        self.cont_grp_season.attrib['groupType'] = "SEASON"
        self.cont_grp_series = ET.SubElement(self.content, "group")
        self.cont_grp_series.attrib['groupId'] = self.series_id
        self.cont_grp_series.attrib['groupType'] = "SERIES"


    def add_chan_details(self, service_id):

        self.chan = ET.SubElement(self.channels, "chan")
        self.chan.attrib['channelId'] = str(service_id)
        region1 = ET.SubElement(self.chan, "region")
        region1.attrib["regionId"] = "East"
        region2 = ET.SubElement(self.chan, "region")
        region2.attrib["regionId"] = "South"
        region3 = ET.SubElement(self.chan, "region")
        region3.attrib["regionId"] = "North"

    def get_program_id(self, title="program"):
        #return str(title)+"-"+str(time.time()).split('.')[0]
        return str(title)+"-"+str(long(time.time()*1000))[5:]

    def get_event_id(self, title="program"):
        #return title+"-"+str(time.time())[:6]+"~"+str(time.time()*100)[6:12]
        return title+"-"+str(long(time.time()*1000))[:5]+'~'+str(long(time.time()*1000))[7:]

    def generate_series_id(self):
        return "SER"+str(random.randint(100, 499))

    def generate_season_id(self):
        return"SEA"+str(random.randint(500, 999))

    def write_xml(self):
        self.indent(self.tree)
        ET.ElementTree(self.tree).write(self.final_xml)
        if self.add_xml_declaration():
            print "Ingest XML file generated and stored in ", os.path.abspath(self.final_xml)
            return os.path.abspath(self.final_xml)
        else:
            print "Error in adding the XML declaration"
            return False

    def post_xml(self, removeXML=True):
        post_status = None

        # write xml
        if not self.write_xml():
            print "Unable to create the ingest xml"
            return False, self.final_xml

        # Create the ingest.json file
        if not self.create_ingest():
            return False, self.final_xml

        # Create the manifest-can.json file
        if not self.create_manifest():
            return False, self.final_xml

        # Post the xml and json files to S3SFTP server
        if sys.argv[1].startswith('aws'):
            print "Ingesting the canonical xml file in s3 bucket at aws environment."
            #bucket = "cdvr-metadata-ingest"
            s3 = boto3.resource("s3")
            for files in self.file_to_push:
                data = open(files, 'rb')
                s3.Bucket(self.bucket).put_object(Key=files, Body=data)
            
        else:
            post_status = self.sftp_put()
            if not post_status:
                print "Unable to post the XML to the S3SFTP server"
                return False, self.final_xml

        if removeXML:
            os.remove(self.final_xml)
            return True, None
        else:
            print "Remove the Ingested file manually from %s" %(str(self.final_xml))
            return True, self.final_xml

    def getTotalLength(self):
        try:
            stime = min(self.startTimeEpoch)
            etime = max(self.endTimeEpoch)
            duration = etime - stime
            return duration
        except:
            return False

    def get_broadcast_end_time(self):
        return self.end_time

    def iso2epoch(self, iso_value):
        """
        Convert the ISO time in "%Y-%m-%dT%H:%M:%SZ" format to EPOC time
        Widely used in Guard time test cases
        :param iso_value:
        :return:
        """
        try:
            epoch_value = calendar.timegm(datetime.datetime.strptime(iso_value, "%Y-%m-%dT%H:%M:%SZ").timetuple())
            return epoch_value
        except ValueError:
            epoch_value = calendar.timegm(datetime.datetime.strptime(iso_value, "%Y-%m-%dT%H:%M:%S.%fZ").timetuple())
            return epoch_value
        except Exception as e:
            print "Error in converting iso to epoch timestamp.\n"+str(e)
            return None

    def epoch2iso(self, epoch_value):
        """
        Convert the EPOCH time to ISO time format %Y-%m-%dT%H:%M:%SZ
        Widely used in manual booking
        :param epoch_value:
        :return:
        """
        try:
            iso_value = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch_value))
            return iso_value
        except Exception as e:
            print "Error in converting epoch to iso timestamp.\n"+str(e)
            return None

    def convert_duration(self, duration_min):
        if duration_min > 0:
            if duration_min > 60:
                hour_count = duration_min / 60
                min_count = duration_min % 60
                duration = "PT%02dH%02dM00S" % (hour_count, min_count)
            else:
                duration = "PT00H%02dM00S" % duration_min
            return duration

        else:
            print "Duration can't be 0 or less than that."
            return "PT00H%02dM00S" % self.default_duration

    def add_xml_declaration(self):
        try:
            line0 = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            with open(self.final_xml, 'rb') as fp:
                rwlines = fp.readlines()
                rwlines.insert(0, line0)
            fp.close()
            with open(self.final_xml, 'w') as fp1:
                for ele in rwlines:
                    fp1.writelines(ele)
                fp1.close()

            return True

        except Exception as e:
            print "Error in adding the XML declaration :", str(e)
            return False

    def indent(self, elem, level=0):
        i = "\n" + level * "  "
        j = "\n" + (level - 1) * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i + "  "
            for subelem in elem:
                self.indent(subelem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = j
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = j + "  "
        return elem

    def create_manifest(self, xml_files=None):
        try:
            data = {}
            data['header'] = {}
            data['header']['fcid'] = "LINEARFEEDJOB_id_"+str(random.randint(10000, 99999))+str(random.randint(1000, 9999))
            data['header']['dataType'] = "Linear"
            data['header']['providerId'] = "cdvr-canonical"
            data['header']['date'] = self.epoch2iso(time.time())

            data['manifest'] ={}
            data['manifest']['schedule'] = []
            if not xml_files:
                xml_files = self.final_xml
            if not isinstance(xml_files, list):
                xml_files = [xml_files]
            for xml in xml_files:
                data['manifest']['schedule'].append(xml)

            jd = json.dumps(data, indent=4, sort_keys=True)
            with open(self.manifest_json, "w") as fp:
                fp.write(jd)
                fp.close()
            print "Manifest file created"
            return True
        except Exception as e:
            print "Error in creating manifest file.\n", str(e)
            return False

    def create_ingest(self):
        try:
            data = {"manifest": "manifest-can.json"}
            jd= json.dumps(data, indent=4, sort_keys=True)
            with open(self.ingest_json, "w") as fp:
                fp.write(jd)
                fp.close()
            print "Ingest file created"
            return True
        except Exception as e:
            print "Error in creating Ingest file.\n", str(e)
            return False


    def sftp_put(self, files_to_push=None):
        try:
            transport = paramiko.Transport((self.sftp_host, self.sftp_port))
            transport.connect(username=self.sftp_user, password=self.sftp_password)

            sftp = paramiko.SFTPClient.from_transport(transport)

            if not files_to_push:
                files_to_push = self.file_to_push
            for files in files_to_push:
                final_path = os.path.join(self.ingest_location, files)
                print "S3 SFTP Path :", final_path
                sftp.put(files, final_path)

            sftp.close()
            transport.close()

            return True

        except Exception as e:
            print "Error in sftp put :", str(e)
            return False


if __name__ == "__main__":
    ch = ChannelLineupV3()

    #print ch.add_event(start_time_delay_mins=3, duration_min=5, service_id=59432, num_of_events=60, event_id_prefix="cisco")
    # O/P : [('program-1497248599', '2017-06-12T06:26:19Z', 'PT00H05M00S', 'program-149724~485992'),
    #        ('program-1497248600', '2017-06-12T06:31:19Z', 'PT00H05M00S', 'program-149724~486002')]

    print ch.add_series(service_id=59432, duration_min=5, episode_count=2, event_id_prefix="cisco")
    print ch.add_series(service_id=10057, duration_min=5, episode_count=3, event_id_prefix="tidel")
    # O/P : {'SER143': [('program-1497248601', '2017-06-12T06:23:21Z', 'PT00H03M00S', 1, 'test-149724~486012'),
    #                   ('program-1497248602', '2017-06-12T06:26:21Z', 'PT00H03M00S', 2, 'test-149724~486022'),
    #                   ('program-1497248603', '2017-06-12T06:29:21Z', 'PT00H03M00S', 3, 'test-149724~486032')]}

    #print "start time :", ch.epoch2iso(ch.start_time)
    #print "end time : ", ch.epoch2iso(ch.end_time)

    #print ch.add_series(service_id=1049, duration_min=3, episode_count=3)

    #print ch.add_series(service_id=55443, duration_min=2, episode_count=5, event_id_prefix="test", gap_mins=5, startepisodenumber=1,
    #                    rebroadcast=[3,5], rebroadcastdealy_mins=10, start_time_delay_mins=15)

    ### Example to ingest 2 episode of a series in a channel and ingest the same series of another 2 episode in another channel
    # custom_series_id = ch.generate_series_id()
    # print ch.add_series(service_id=59432, duration_min=5, episode_count=2, event_id_prefix="cisco", series_id=custom_series_id)

    end_time = ch.getTotalLength()
    print "Total length :", end_time
   
    # print ch.add_series(start_time_delay_mins=end_time/60, service_id=10057, duration_min=5, episode_count=2, event_id_prefix="cisco", series_id=custom_series_id) 
   
    ### end of example ###   
   
    print "Ingest File :", ch.final_xml
    ch.write_xml()
    ## print ch.post_xml(removeXML=False)


