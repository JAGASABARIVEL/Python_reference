import sys
import time
import inspect
import os
import re


class PyTee(object):
    def __init__(self, *files):
        self.files = files
        
    def write(self, output):
        for f in self.files:
            f.write(output)

    def get_file(self):
        _file = self.files[-1]
        _file.close()
        return _file.name

def enable_logging(logdir=None, filename=None, mode='w'):
    userHomeDir = os.path.expanduser("~")
    if logdir == None:
        logdir = os.path.join(userHomeDir, "cdvr_automation_log")

    _org = sys.stdout
    if isinstance(_org, PyTee):
        return None
    

    try:
        if os.path.isdir(logdir) is False:
            os.makedirs(logdir)
    except Exception as e:
        # if unable to create directory, lets move on to just use stdout
        print "WARNING: File logging disabled because of the following reason"
        print "WARNING: Unable to create directory: %s" % logdir
        return None

    logFile = filename
    
    if logFile == None:
        timestr = time.strftime("%H%M%S-%Y%m%d")
        frame = inspect.stack()[-1]
        module = inspect.getmodule(frame[0])
        filePath = module.__file__
        _filename = os.path.basename(filePath)
        filename = re.sub(r'\..*$', '', _filename)
        #fullFileName = filename + '_' + timestr + ".log"
        fullFileName = filename + ".log"
        logFile = os.path.join(logdir, fullFileName)
        
    f = open(logFile, mode)
    sys.stdout = PyTee(sys.stdout, f)
    sys.stderr = sys.stdout
