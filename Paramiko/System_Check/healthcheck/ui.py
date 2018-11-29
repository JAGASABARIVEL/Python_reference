import time
import sys


class UI(object):

    def __init__(self):
        self.maxtime = 100
        self.progressname = ""

    def setProgress(self, progress):
        if isinstance(progress, int):
            progress = float(progress)
        if progress < 0:
            progress = 0
        if progress >= 1:
            progress = 1
        self.covered = int(round(self.maxtime * progress))
        display = "\r{2}: [{0}] {1}%".format("#" *
                                             self.covered +
                                             "-" *
                                             (self.maxtime -
                                              self.covered), progress *
                                             100, self.progressname)
        sys.stdout.write(display)
        sys.stdout.flush()


if __name__ == '__main__':
    pass

################## USSAGE ######################
#	UI = UI()
#	i = 0
#	while i < 100:
#	    time.sleep(0.1)
#           i += 1
#	    UI.setProgress(i/100.0)
#
