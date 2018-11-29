#!/usr/bin/env python

USAGE="""\

       *********************************************************
                               IMPORTANT
       This module has dependencies specified in requirement.txt.
       Please install the dependencies before using this module.
       PERFORM ==> pip install -r requirements.txt
       *********************************************************

Usage:
  -M  --Mode        Mode on which script to be run.
  -TC --TestCase    Testcases to be modified.
  -TA --TagAdd      Tags that are to be added to the testcases.
  -TR --TagRemove   Tags that are to be removed from testcases.

Syntax  : python rally_modify_tags.py -M <mode> -TC <testcases> \
              -TA <tags_to_be_added> -TR <tags_to_be_removed>
Example:
    For batch input,
        python rally_modify_tags.py -M batch -TC testcases.txt \
            -TA tagstobeadded.txt -TR tagstoberemoved.txt
    For single input,
        python rally_modify_tags.py -M non-batch -TC TC10130 \
            -TA brb_phase2 -TR Master
"""

import time
import argparse
from threading import Thread
from multiprocessing import Process
import urllib3
import yaml
from pyral import Rally
import pyral_fixes # This will provide an fix for the found bugs in pyral
from rallylib import config

# ------------------ GLOBAL CONSTANTS ---------------- #
APIKEY = str(config("APIKEY"))
WORKSPACE = str(config("WORKSPACE"))
PROJECT = str(config("PROJECT"))
RALLYURL = str(config("RALLYURL"))
# ---------------------------------------------------- #

# List of TestCases stored in this objectr for global visibility.
TESTCASELIST = []
# List of modes allowed.
ALLOWEDMODES = ["batch", "non-batch"]
# Similar to queue in threading but here it actually controls
# how many items to be processed in single thread.
QUEUELENGTH = 5

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RallyModifyTags(object):
    """
    Class that does the operation on the entity's Tags.
    """
    def __init__(self):
        self.tags = []
        self.parse_arguments()
        self.make_objects(self.args.Mode, self.args.TestCase, self.args.TagAdd, self.args.TagRemove)

    def parse_arguments(self):
        """
        Routine that parse the argument and retrives locally.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("-M", "--Mode", type=str, \
                        help='Mode on which script to be run.')
        parser.add_argument("-TC", "--TestCase", type=str, \
                        help='Testcases to be modified')
        parser.add_argument("-TA", "--TagAdd", type=str, \
                        help='Tags that are to be added to the testcases.')
        parser.add_argument("-TR", "--TagRemove", type=str, \
                        help='Tags that are to be removed from testcases.')
        self.args = parser.parse_args()
        if self.args.Mode not in ALLOWEDMODES or not self.args.Mode:
            print "Invalid mode selection."
            print "Please use any of the following mode %s." % (ALLOWEDMODES)
            print USAGE
            exit(0)
        if not self.args.TestCase or not self.args.TagAdd:
            print "Missing TestCase argument or TagAdd argument or both."
            print "Please provide the TestCase and TagAdd argument."
            print USAGE
            exit(0)

    def make_objects(self, typer, tcobject, tagaddobject, tagremoveobject):
        """
        Routine that forms the list object from the user input.
        """
        if typer == ALLOWEDMODES[1]:
            self.testcases = [tcobject,]
            self.tag_names_to_be_added = [tagaddobject,]
            if self.args.TagRemove: self.tag_names_to_be_dropped = [tagremoveobject,]
            else: self.tag_names_to_be_dropped = []
        else:
            self.testcases = self.read_n_return_list_object(tcobject)
            self.tag_names_to_be_added = self.read_n_return_list_object(tagaddobject)
            if self.args.TagRemove: self.tag_names_to_be_dropped = \
                self.read_n_return_list_object(tagremoveobject)
            else: self.tag_names_to_be_dropped = []

    def get_list(self, list_name):
        """
        Routine that returns the formed list object based on the respective request.
        """
        if list_name == "testcase": return self.testcases
        elif list_name == "addedtags": return self.tag_names_to_be_added
        elif list_name == "removedtags": return self.tag_names_to_be_dropped

    def set_list(self, list_name, value):
        """
        Routine that allows the formed list object to be overridden.
        """
        if list_name == "testcase": self.testcases = value
        elif list_name == "addedtags": self.tag_names_to_be_added = value
        elif list_name == "removedtags":
            if self.args.TagRemove: self.tag_names_to_be_dropped = value
            else: self.tag_names_to_be_dropped = []

    def read_n_return_list_object(self, filename):
        """
        Routine that reads the file object and returns the list object.
        """
        list_object = []
        with open(filename, "r") as read_descriptor:
            for trace in read_descriptor.readlines():
                list_object.append(trace.strip('\n'))
        return list_object

    def drop_tag(self, entity):
        """
        Core Routine that is responsible for removing the tag from the entity.
        """
        droppable_tags = []
        for tag in self.tags:
            if tag.Name in self.tag_names_to_be_dropped:
                droppable_tags.append(tag)
        drops = self.rally.dropCollectionItems(entity, droppable_tags)
        return bool(drops.status_code == 200)

    def add_tag(self, entity):
        """
        Core Routine that is responsible for removing the tag from the entity.
        """
        add_tags = []
        for tag in self.tags:
            if tag.Name in self.tag_names_to_be_added:
                add_tags.append(tag)
        adds = self.rally.addCollectionItems(entity, add_tags)
        return bool(adds[0].status_code == 200)

    def connect_n_edit_tags(self, testcase):
        drops = True # Setting it as True to handle drop results as it is optional argument
        """
        Call back routine for each thread.
        """
        self.story_id = testcase
        self.collective_tags = self.tag_names_to_be_added + self.tag_names_to_be_dropped
        self.story = self.rally.get('TestCase', fetch="FormattedID,Name,Description,Tags",\
                           query="FormattedID = %s" % self.story_id,\
                           server_ping=False, isolated_workspace=True, instance=True)

        self.response = self.rally.get('Tag', fetch="true", \
            order="Name", server_ping=False, isolated_workspace=True)
        for tag in self.response:
            #print "Workspace %s  has tag: %-14.14s created on %s  Name: %s"  % \
            #      (tag.Workspace.Name, tag.oid, tag.CreationDate[:-5].replace('T', ' '), tag.Name)
            if tag.Name in self.collective_tags:
                self.tags.append(tag)

        _cache_available_tag_names = [tag.Name for tag in self.tags]
        for tag_name in self.tag_names_to_be_added:
            if tag_name not in _cache_available_tag_names:
                print "Creating a new tag %s since the tag does not exist." % (tag_name)
                tag_create = self.rally.create('Tag', dict(Name=tag_name))
                self.tags.append(tag_create)
        _cache_available_tag_names = [tag.Name for tag in self.tags]

        if self.story:
            if self.args.TagRemove:
                drops = self.drop_tag(self.story)
            adds = self.add_tag(self.story)
            if adds is True and drops is True:
                return True
        return False

    def trigger_engine(self):
        """
        Entry point routine that forms the connection object to rally
        Triggers the call back routine connect_n_edit_tags.
        """
        status = 'FAIL'
        self.rally = Rally(RALLYURL, apikey=APIKEY, workspace=WORKSPACE,\
                project=PROJECT, verify_ssl_cert=False)
        for testcase in self.testcases:
            if self.connect_n_edit_tags(testcase) is True:
                status = "OK"
            print "Updated the entity %s \t ...\t [%s]" % (testcase, status)

def instance_action(index):
    """
    Routine that connects to the class RallyModifyTags
    This in turn will be triggered by each thread.
    """
    _instance = RallyModifyTags()
    _instance.set_list("testcase", TESTCASELIST[index:index+QUEUELENGTH])
    _instance.trigger_engine()
    del _instance

if __name__ == '__main__':
    instance = RallyModifyTags()
    TESTCASELIST = instance.get_list("testcase")
    testcase_count = len(TESTCASELIST)
    flag =  instance.args.Mode
    if flag == ALLOWEDMODES[1]:
        instance_action(0)
    else:
        for index in range(0, testcase_count, QUEUELENGTH):
            t = Thread(target=instance_action, args=(index,))
            t.start()
            # Join to avoid corruption in rally connection object.
            t.join()
