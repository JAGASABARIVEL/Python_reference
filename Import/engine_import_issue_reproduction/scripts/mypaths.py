'''
    Module to set path for script-specific imports

    Usage:  import mypaths
            import script_specific  # like L1commonFunctions
'''
import os
import sys

# last in list becomes first in python search path
include_these_dirs = [
    "v2_folder",
    "lib",
    "v3_folder"
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
    raise  ImportError("unexpected directory layout")
scriptDir = scriptDir[:index+len(expected_dir)]

for d in include_these_dirs:
    if scriptDir + d not in sys.path:
        sys.path.insert(0,scriptDir + d)

print  "sys.path : ", sys.path
