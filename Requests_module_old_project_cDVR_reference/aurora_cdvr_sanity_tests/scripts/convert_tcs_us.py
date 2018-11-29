#!/usr/bin/python

import csv
import os
import shutil
import re
import glob

def convert_filename_keywords():
    keywordchangecounter = 0
    directory = os.getcwd()
    print directory
    try:
        '''with open('mapping2.csv', mode='r') as infile:
            reader = csv.reader(infile)
            mydict = dict((rows[0],rows[1]) for rows in reader)
        subdirs = [x[0] for x in os.walk(directory)]
        print subdirs 
        for src,tgt in mydict.iteritems():
            for subdir in subdirs:
                files = os.walk(subdir).next()[2]
                if (len(files) > 0):
                    for f in files:
                        if f.find(src)!=-1:
                            print f
                            source = os.path.join(subdir,f)
                            new_filename = f.replace('_'+src+'_', '_'+tgt+'_')
                            new_filename = f.replace('_'+src, '_'+tgt)
                            new_filename = f.replace(src, tgt)
                            print new_filename
                            target = os.path.join(subdir,new_filename)
                            os.rename(source,target)
        for subdir in subdirs:
            files = os.walk(subdir).next()[2]
            if (len(files)>0):
                for f in files:
                    print f
                    fname = os.path.join(subdir,f)
                    if fname.endswith(".py"):
                        print fname
                        fo = open(fname, "rU+")
                        text = fo.read()
                        for src, target in mydict.iteritems():
                            text = text.replace(src, target)
                        fo.seek(0)          
                        fo.write(text)
                        fo.truncate()
                        fo.close()
                        keywordchangecounter += 1
        if keywordchangecounter:
            print "Conversion done successfully"
            return 0
        else:
            print "No Conversion done"
            return 1'''
        with open('testfile.csv', mode='r') as infile:
            reader = csv.reader(infile)
            mydict = list(rows[0] for rows in reader)
        outfile = open('lntout.csv', mode='w')
  
        subdirs = [x[0] for x in os.walk(directory)]
        mylist = []
        
        for subdir in subdirs:
            files = os.walk(subdir).next()[2]
            if (len(files)>0):
                for f in files:
                    fname = os.path.join(subdir,f)
                    if fname.endswith(".py"):
                        fo = open(fname, "rU+")
                        text = fo.read()
                        for src in mydict:
                            if src in text:
                                print src,"-->","Yes"
                                mylist.append((src,"yes"))
                            else:
                                print src,"-->","No"
                        fo.truncate()
                        fo.close()
        print mylist
        print len(mylist)
        for x in mylist:
            outfile.write(x[0]+","+x[1]+"\n")
    except Exception as e:
        print str(e)
        pass

if __name__ == '__main__':
    L = convert_filename_keywords()
    exit(L)
     

