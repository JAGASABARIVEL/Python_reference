# Scripts
These scripts take 1 or 2 arguments. The first arg is a labname which boils down to a directory which must exist in the config directory. The optional 2nd arg is a file containing yaml which overrides the yaml defined by the labname.

I've highlighted a few main ones below. Some are simply imported by others which I won't get into.

## sanity
This script is intended to be called first to check the sanity of the system.  It runs **sanity\_\*.py** scripts, in alphabetical order, and ensures the _sanity\_create\_household.py_ runs first. Each sanity\_\*.py script should be written in such a way as to be able to run on its own as well as be imported by the sanity script. Each sanity\_\*.py script must supply a _doit(cfg)_ function which will be called by the sanity script where cfg is the structure returned by reading in the yaml configs.

## basic-feature
This script runs the basic feature tests defined. It uses the same configuration, runs the same "doit" method defined in each, as described above in sanity section.

## corner
This scripts runs the corner case tests defined. It uses the same configuration, runs the same "doit" method defined in each, as described above in sanity section.

## cdvr\_automation
This script runs the test suite: sanity first, if it passes, then basic-feature, and if it passes, corner case tests. There are lab-specific configuration which can be utilized to define which combination of these 3 will run.

## showcfg
Just a useful utility script to output the configuration structure.

## delete\_household.py
_Be careful when this script is run if only supplying the lab name as argument, since it is possible that CI/CD pipeline is using these households as well._ 
