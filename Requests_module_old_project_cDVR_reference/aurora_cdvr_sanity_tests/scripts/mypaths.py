'''
    Module to set path for script-specific imports

    Usage:  import mypaths
            import script_specific  # like L1commonFunctions
'''
import os
import sys

# last in list becomes first in python search path
include_these_dirs = [
    "performance_scripts",
    "cornercase_scripts",
    "basic_feature_scripts",
    "sanity_scripts",
    "lib",
    "lib" + os.sep + "channellineup",
    "longterm_basic_feature_start",
    "longterm_basic_feature_verify",
    "longterm_cornercase_start",
    "longterm_cornercase_verify",
    "basic_feature_scripts_ppsv3",
    "cornercase_set1_ppsv3",
    "sanity_scripts_ppsv3",
    "sanity_scripts_ppsv3/healthcheck",
    "cornercase_scripts_ppsv3",
    "feature_scripts",
    "feature_scripts/brb",
    "feature_scripts/brb_phase2"
]

abspath = os.path.abspath(__file__)
scriptName = os.path.basename(__file__)
scriptDir = os.path.dirname(abspath)
scriptDir += os.sep

# find the scripts portion of the path
# TODO potential bug if /scripts/ exists more than once in path
expected_dir = os.sep + "scripts" + os.sep
index = scriptDir.find(expected_dir)
if index < 0:
    raise ImportError("unexpected directory layout")
scriptDir = scriptDir[:index+len(expected_dir)]

for d in include_these_dirs:
    if scriptDir + d not in sys.path:
        sys.path.insert(0, scriptDir + d)
