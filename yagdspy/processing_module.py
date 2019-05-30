# Copyright 2016, 2017, 2019 Fred Hutchinson Cancer Research Center
################################################################################
### Framework of processing module method


import os
import re
import inspect
import datetime

import boto3

processing_module_info = []


from .eval_processing_graph import *


def is_s3_url(filename):
    if len(filename) > 5:
        if "s3://" == filename[:5]:
            return True
    return False

def s3_check_modified_time(url):
    """Return timestamp if object exists"""
    
    s3client = boto3.client('s3') 
    m = re.search("\As3://([^/]+)/(.+)\Z", url)
    if None == m:
        raise Exception("ERROR url does not seem to be a valid AWS S3 url: " + url)
    bucket, key = m.groups()
    try:
        metadata = s3client.head_object(Bucket=bucket, Key=key)
    except:
        return False, None

    modified_text = metadata['ResponseMetadata']['HTTPHeaders']['last-modified']
    d = datetime.datetime.strptime(modified_text, "%a, %d %b %Y %H:%M:%S %Z")
    return True, d.timestamp() # get time since epoch like os.path.getmtime()


def is_readable(filename):
    return os.access(filename,  os.R_OK)


def check_modified_time(filename):
    if is_s3_url(filename):
        return s3_check_modified_time(filename)
    elif is_readable(filename):
        return True, os.path.getmtime(filename)
    else:
        return False, None


class ProcessingModule:
    """Define basic idea of processing module class to be something that
    has a set of required files, and provides a set of files, while doing
    some kind of computation in the middle"""

    def __init__(self, base, config):
        self.base = base;
        self.config = config
        self.requires = set()
        self.provides = set()
        self.sub_modules = []
        self.name = "unknown, needs to be set"


    def __str__(self):
        return self.name;


    def check_exist(self, fileset, required):
        timestamps = []
        exists = True
        for filename in fileset:
            it_exists, timestamp = check_modified_time(filename)
            if it_exists:
                timestamps.append(timestamp)
            else:
                exists = False
                if required:
                    raise Exception("ERROR could not read" + filename);

        return exists, timestamps

    def check_prereqs(self, required=True):
        return self.check_exist(self.requires, required)

    def check_postreqs(self, required=True):
        return self.check_exist(self.provides, required)

    def add_submodule(self, module):
        self.sub_modules.append(module)

    def inspect_internal_graph(self):
        self.D = generate_processing_graph(self.sub_modules)
        for item in self.D.find_sources():
            self.requires.add(item)
        for item in self.D.find_sinks():
            self.provides.add(item)



    def process_internal_graph(self):
        sorter = TopologicalSort(self.D)
        order = sorter.topological_sort()
        for item in order:
            if not isinstance(item, ProcessingModule):
                continue;
            item.process()




def boundaryCheck1(f):
    def checking_version(self):
        self.check_prereqs()
        f(self)
        self.check_postreqs()
    return checking_version

def boundaryCheck(f):
    def skipping_version(self, dry_run=False):
        if dry_run:
            pre_exist, pre_timestamps = self.check_prereqs(required=False)
            post_exist, post_timestamps = self.check_postreqs(required=False)
            if not pre_exist:
                print('[Dry Run] prereqs are not present for ' + self.name)
                return
            if post_exist and min(post_timestamps) > max(pre_timestamps):
                print("[Dry Run] Provide files up-to-date, will skip " + self.name)
                return;
            print('[Dry Run] Would need to run ' + self.name)
            return
            
        pre_exist, pre_timestamps = self.check_prereqs()
        post_exist, post_timestamps = self.check_postreqs(required=False)
        if post_exist and min(post_timestamps) > max(pre_timestamps):
            # can skip
            print("Provide files up-to-date, will skip " + self.name)
            return;

        print("Running " + self.name)
        f(self)
        self.check_postreqs()
    return skipping_version





def parse_file_templates(file_dictionary):
    """Parse input/output file path templates"""
    inputs = {}
    outputs = {}

    for varname, pathname in file_dictionary.items():
        if varname.startswith("in "):
            key = varname.split('in ')[1]
            inputs[key] = pathname

        elif varname.startswith("in| "):
            key = varname.split('in| ')[1]
            inputs[key] = pathname

        elif varname.startswith('out '):
            key = varname.split('out ')[1]
            outputs[key] = pathname

        elif 'base' == varname or 'config' == varname:
            continue;
        else:
            raise Exception("Unexpected files arg:" + varname)
    return inputs, outputs




def create_processing_module(func, name=None, files=None):
    """For specially definined functions, create a processing module class for them, as
    a convenience. Requirements:
      * The function must only take keyword arguments.
      * The keyword arguments refer to files or directories mostly
      * If it is a file the function creates, the files key starts with "out " 
      * If it is a file the function requires, the files key starts with "in ", and has a relative path
      * If it is a file the function requires, the files key starts with "in| ", and has an absolute path

    The function must also have a base and config keyword for those
    objects, but those do not need to be in the files dictionary

    The relative-path files are assumed to be relative to config['OUTPUT_DIR']
    Returns a classobj

    The relative/absolute path names may be templates, containing say
    {project}, which will be expanded using the contents of the config
    dictionary.

    """


    inputs, outputs = parse_file_templates(files)


    class Wrap(ProcessingModule):
        def __init__(self, base, config):
            ProcessingModule.__init__(self, base, config)
            self.name = func.__name__ if None == name else name
            self.files = {}
            self.func = func;

            func_args = set(inspect.getargs(func.__code__).args)
            def check_arg(argname):
                if argname not in func_args:
                        raise Exception("ERROR implementation function " + func.__name__ + 
                                        " does not have " + argname + " keyword parameter")


            if 'base' not in func_args:
                raise Exception("ERROR implementation function " + func.__name__ + " does not have base keyword parameter")
            if 'config' not in func_args:
                raise Exception("ERROR implementation function " + func.__name__ + " does not have config keyword parameter")


            for key, pathname in inputs.items():
                fullname = pathname.format(**config)
                self.requires.add(fullname)
                self.files[key] = fullname
                check_arg(key)
                setattr(self, key, self.files[key])

            for key, pathname in outputs.items():
                fullname = pathname.format(**config)
                self.provides.add(fullname)
                self.files[key] = fullname
                check_arg(key)
                setattr(self, key, self.files[key])
                  

        @boundaryCheck
        def process(self):
            # automatically create output directories ???
            args = { k:i for k,i in self.files.items() }
            args['base'] = self.base
            args['config'] = self.config
            self.func(**args)

    processing_module_info.append((name, Wrap, inputs, outputs))
    return Wrap






def check_requirements(requirements):
    requirements_met = True;
    msg = "";
    for r in requirements:
        if isinstance(r, ProcessingModule):
            raise Exception("ERROR problem in graph where a processing module is a source requirement")

        exists, timestamp = check_modified_time(r)
        if not exists:
            msg += "ERROR not found " + r + "\n"
            requirements_met = False;
        else:
            print('Found ' + r)
    if not requirements_met:
        raise Exception(msg)


def make_it_go(L, output_graph=None, dry_run=False):
    D = generate_processing_graph(L)
    if None != output_graph:
        plot_graph(output_graph, D)

    # check
    requirements = D.find_sources() # find_initial_dependancies
    check_requirements(requirements)
    sorter = TopologicalSort(D)
    order = sorter.topological_sort()

    for item in order:
        if not isinstance(item, ProcessingModule):
            continue;
        item.process(dry_run=dry_run)
