'''
Class and methods to read/write json file

Handles updates to file of json data by loading, then dumping changes.

Running as main will create a sample_ec_results.json file which you can view pretty:

    cat sample_ec_results.json | python -mjson.tool
    
    or

    python -mjson.tool sample_ec_results.json

Ken Shaffer
'''
import os
import json

class JsonReadWrite(object):
    def __init__(self, filename=None, deleteIfPresent=False, indent=4):
        '''
        init class by passing in
        :param filename: name of file to store json data
        :param deleteIfPresent: set True to delete the file first if present
        :param indent: indentation in json file for prettyness (None for compact)
        :return: an instance of JsonReadWrite class

        Removes pre-existing filename if deleteIfPresent is True.

        instance saves the filename and indentation desired
        '''
        self.indent = indent
        if filename == None:
            raise OSError("Missing filename")
        self.filename = filename
        if deleteIfPresent:
            try:
                stat_results = os.stat(filename)
                os.remove(filename)
            except (IOError, OSError):
                pass

        # create empty dict, aka json object, if not present
        try:
            stat_results = os.stat(filename)
        except OSError:
            self._initial_create({})

        self.filename = os.path.abspath(filename)

    def _initial_create(self, obj):
        ''' internal method to create the file first '''
        fp = open(self.filename, mode='w')
        json.dump(obj,fp, indent=self.indent)
        fp.close()

    def __str__(self):
        return self.filename

    # courtesy of http://stackoverflow.com/questions/823196/yaml-merge-in-python
    def _merge_dict(self, new, current):
        ''' internal method to merge a new dict with a current dict '''
        if isinstance(new, dict) and isinstance(current, dict):
            for k,v in current.iteritems():
                if k not in new:
                    new[k] = v
                else:
                    new[k] = self._merge_dict(new[k],v)
        return new

    def writeDictJson(self, new_obj):
        '''
        Write the new_obj dict at the root level

        :param new_obj: dict
        :return:

        Opens filename for reading and json loads it, then merges the new_obj,
        then writes the merged obj back to filename by json dump using desired
        indentation, and closes the file.

        '''
        # first read what we have
        fp = open(self.filename, mode='r')
        current_obj = json.load(fp)
        fp.close()

        # now merge in the additions and write back out
        new_obj = self._merge_dict(new_obj, current_obj)
        fp = open(self.filename, mode='w')
        json.dump(new_obj, fp, indent=self.indent)
        fp.close()

    def appendListToKey(self, key, new_list):
        '''
        Method to append a list to another dicts list

        :param key:  string of keys separated by colon to locate dict of list
                     example: 'testsuite:basic-feature'

        :param new_list: the new list to append to given key
        :return:

        Opens filename for reading and json loads it, splits the key into
        python dict update by key, presumes the key refers to a list, appends
        new_list to it, then writes the merged obj back to filename by json 
        dump using desired indentation, and closes the file.

        '''
        # first read what we have
        fp = open(self.filename, mode='r')
        current_obj = json.load(fp)
        fp.close()

        # now append in the additions and write back out
        key_sub = "['" + "']['".join(str(key).split(':')) + "']"
        try:
            exec('current_obj'+key_sub+'.append(new_list)')
        except:
            # keys don't exist so create them pointing to other dicts except for the last as a list
            default_key_sub = ".setdefault('" + "',{}).setdefault('".join(str(key).split(':')) + "',[])"
            exec('current_obj'+default_key_sub)
            # now that the dicts are present, try again
            exec('current_obj'+key_sub+'.append(new_list)')
        fp = open(self.filename, mode='w')
        json.dump(current_obj, fp, indent=self.indent)
        fp.close()

if __name__ == "__main__":
    # fresh start, ensure results file deleted
    my_sanity_results = JsonReadWrite('sample_ec_results.json',deleteIfPresent=True)
    # write out config
    configObj = {
        "config":{
            "description": "Integration lab on VDC3",
            "extraconf": "None",
            "gitlastcommit": "bbb3f3b1229",
            "gitrepo": "origin\thttps://bitbucket-eng-rtp1.cisco.com/bitbucket/scm/ihdev/aurora_cdvr_sanity_tests.git (fetch)",
            "labname": "lwr_integration"
        }
    }
    my_sanity_results.writeDictJson(configObj)

    # add a sanity result
    results1 = {
        "CF": "",
        "I": "Core DVR Functionality",
        "MF": "",
        "US": "Create Household along with device.",
        "message": "Sanity tests completed successfully.",
        "name": "sanity",
        "status": "PASS",
        "time": "25.7953"
    }
    my_sanity_results.appendListToKey('testsuite:sanity', results1)

    # simulate another test file run, this time basic-feature, note no delete if present
    my_basicfeature_results = JsonReadWrite('sample_ec_results.json')

    results2 = {
        "CF": "",
        "I": "Core DVR Functionality",
        "MF": "",
        "US": "Create Household along with device.",
        "message": "Household created successfully.",
        "name": "basic_create_household",
        "status": "PASS",
        "time": "12.17953"
    }
    my_basicfeature_results.appendListToKey('testsuite:basic-feature', results2)

    results2 = {
        "CF": "",
        "I": "Core DVR Functionality",
        "MF": "",
        "US": "Get catalog services.",
        "message": "Catalog services retrieved successfully.",
        "name": "basic_0010_getCatalogServices",
        "status": "PASS",
        "time": "2.5967"
    }
    my_basicfeature_results.appendListToKey('testsuite:basic-feature', results2)
