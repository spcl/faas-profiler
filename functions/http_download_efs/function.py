#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A AWS Lambda function.
"""

import py_faas_profiler as fp
from os import listdir
from os.path import join, abspath, dirname, basename
from shutil import copyfile

config_file = join(abspath(dirname(__file__)), "fp_config.yml")


@fp.profile(config_file=config_file)
def handler(event, context):
    print(listdir("/mnt/access"))

    copyfile(
        src=join(abspath(dirname(__file__)), "server.jpg"),
        dst='/mnt/access/server.jpg')
    
    print(listdir("/mnt/access"))

    return {
        "message": "done"
    }
