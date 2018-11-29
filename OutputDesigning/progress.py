#!/usr/bin/python

import sys
import time

TotalProgress = 100

#sys.stdout.write("[%s]"% (" " * TotalProgress))
#sys.stdout.flush()
#sys.stdout.write("\b" * (TotalProgress+1))

counter = 0
for bar in xrange(TotalProgress):
    if counter == 0:
        pr = '\\'
        counter += 1
    elif counter == 1:
        pr = "|"
        counter += 1
    elif counter == 2:
        pr = "/"
        counter += 1
    elif counter == 3:
        pr = "-"
        counter += 1
    elif counter == 4:
        pr = "\\"
        counter += 1
    elif counter == 5:
        pr = "|"
        counter += 1
    elif counter == 6:
        pr = "/"
        counter += 1
    elif counter == 7:
        pr = "-"
        counter = 0
    time.sleep(1)
    sys.stdout.write(pr)
    sys.stdout.flush()
    sys.stdout.write('\b' * 1)

sys.stdout.write("\n")
