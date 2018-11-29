import os
#Find the StringA and Replace with StringB in full directory for all python files
replacements = {'StringA':'StringB'}
for files in os.listdir("."):
    if files.endswith(".py"):
        fo = open(files, "rU+")
        text = fo.read()
        for src, target in replacements.iteritems():
                text = text.replace(src, target)
        print replacements
        fo.seek(0)
        fo.write(text)
        fo.truncate()
        fo.close()
#Add the StringA into the specific line no in full directory on all python files
'''exp = 20 # the line where text need to be added or exp that calculates it for ex %2
for files in os.listdir("."):
    if files.endswith(".py"):
        with open(files, 'r') as f:
            lines = f.readlines()
        with open(files, 'w') as f:
            for i,line in enumerate(lines):
                if i == exp:
                    f.write('StringA')
                f.write(line)'''
