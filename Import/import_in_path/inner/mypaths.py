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
    # "cornercase_scripts/cornercase_set1_scripts",
    # "cornercase_scripts/cornercase_set2_scripts",
    # "cornercase_scripts/cornercase_set3_scripts",
    "basic_feature_scripts",
    "sanity_scripts",
    "lib",
    "lib/channellineup",
    "longterm_start_scripts",
    "longterm_verify_scripts",
    "sanity_scripts_ppsv3",
    "basic_feature_scripts_ppsv3",
    "cornercase_scripts_ppsv3",
    # "cornercase_scripts_ppsv3\\cornercase_set1_scripts",
    # "cornercase_scripts_ppsv3\\cornercase_set2_scripts",
    "../"
]

if os.name != "nt":
    include_these_dirs.extend([
        "cornercase_scripts/cornercase_set1_scripts",
        "cornercase_scripts/cornercase_set2_scripts",
        "cornercase_scripts/cornercase_set3_scripts",
        "cornercase_scripts_ppsv3/cornercase_set1_scripts",
        "cornercase_scripts_ppsv3/cornercase_set2_scripts",
        "cornercase_scripts_ppsv3/cornercase_set3_scripts",
    ])
else:
    include_these_dirs.extend([
        "cornercase_scripts\\cornercase_set1_scripts",
        "cornercase_scripts\\cornercase_set2_scripts",
        "cornercase_scripts\\cornercase_set3_scripts",
        "cornercase_scripts_ppsv3\\cornercase_set1_scripts",
        "cornercase_scripts_ppsv3\\cornercase_set2_scripts",
        "cornercase_scripts_ppsv3\\cornercase_set3_scripts",
    ])

ABSPATH = os.path.abspath(__file__)
SCRIPTNAME = os.path.basename(__file__)
scriptDir = os.path.dirname(ABSPATH)
scriptDir += os.sep

# find the scripts portion of the path
# TODO potential bug if /scripts/ exists more than once in path
expected_dir = os.sep + "scripts" + os.sep
index = scriptDir.find(expected_dir)
if index < 0:
    raise ImportError("unexpected directory layout")
scriptDir = scriptDir[:index + len(expected_dir)]

for d in include_these_dirs:
    if scriptDir + d not in sys.path:
        sys.path.insert(0, scriptDir + d)
