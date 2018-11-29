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
    "lib",
    "lib" + os.sep + "channellineup",
    ".." + os.sep
]

v3_dirs = [
    "sanity_scripts_ppsv3",
    "basic_feature_scripts_ppsv3",
    "cornercase_scripts_ppsv3",
    "cornercase_scripts_ppsv3" + os.sep + "cornercase_set1_scripts",
    "cornercase_scripts_ppsv3" + os.sep + "cornercase_set2_scripts",
    "cornercase_scripts_ppsv3" + os.sep + "cornercase_set3_scripts",
]

v2_dirs = [
    "sanity_scripts",
    "basic_feature_scripts",
    "cornercase_scripts",
    "cornercase_scripts" + os.sep + "cornercase_set1_scripts",
    "cornercase_scripts" + os.sep + "cornercase_set2_scripts",
    "cornercase_scripts" + os.sep + "cornercase_set3_scripts",
    "longterm_start_scripts",
    "longterm_verify_scripts",
    "feature_scripts",
    "feature_scripts" + os.sep + "brb",
    "feature_scripts" + os.sep + "brb_phase2",
    "hitless_upgrade_scripts",
    "feature_scripts" + os.sep + "stand_alone",
]


def set_paths(v_path=None):
    abspath = os.path.abspath(__file__)
    scriptName = os.path.basename(__file__)
    scriptDir = os.path.dirname(abspath)
    scriptDir += os.sep

    # find the scripts portion of the path
    # TODO potential bug if /scripts/ exists more than once in path
    expected_dir = os.sep + "scripts" + os.sep
    index = scriptDir.find(expected_dir)
    if index < 0:
        raise  ImportError("unexpected directory layout")
    scriptDir = scriptDir[:index+len(expected_dir)]

    if v_path and v_path == "v2":
        include_these_dirs.extend(v2_dirs)
    elif v_path and v_path == "v3":
        include_these_dirs.extend(v3_dirs)

    for d in include_these_dirs:
        if scriptDir + d not in sys.path:
            sys.path.insert(0,scriptDir + d)

set_paths()
