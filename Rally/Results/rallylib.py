#/usr/bin/python

import os
import yaml

RALLY_KEY = "rally"
TEAM_KEY = "republic-cruiser"
SCRIPT_INDEX = 3
SETTINGS_DIR = "settings"
SETTINGS_FILE = "settings.yaml"

class config(object):
    """
    Class that returns the configuration 
    settings requested by the caller.
    """
    def __init__(self, key_to_find_in_settings):
        self._get_config_path()
        self.key_to_find_in_settings = key_to_find_in_settings
        with open(CONFIGURATION_FILE, 'r') as stream:
            self.return_value = yaml.load(stream)

    def _get_config_path(self):
        global CONFIGURATION_FILE
        _directory_list = (os.path.dirname(os.path.realpath(__file__))).split(os.path.sep)
        HOME_DIR = _directory_list[:len(_directory_list) - SCRIPT_INDEX]
        HOME_DIR = os.path.sep.join(HOME_DIR)
        CONFIGURATION_FILE = os.path.join(HOME_DIR, SETTINGS_DIR, SETTINGS_FILE)

    def __repr__(self):
        return self.return_value[RALLY_KEY][TEAM_KEY][self.key_to_find_in_settings]

