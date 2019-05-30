# Copyright 2016, 2017 Fred Hutchinson Cancer Research Center
################################################################################
### Support planning operations


import re
from .processing_module import *



def regex_ize(pathname_template):
    """Return regex pattern to try to match to pathname template, that use curly braces for arguments"""
    values = re.split("{[^}]+}", pathname_template)
    return '\A' + '.+'.join(values) + '\Z'


def suggest_module(out_file):
    results = []
    for name, module, inputs, outputs in processing_module_info:
        for v in outputs.values():
            pattern = regex_ize(v)
            m = re.search(pattern, out_file)
            if None != m:
                results.append(name)
    return results

