#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A AWS Lambda function.
"""

import py_faas_profiler as fp
from os.path import join, abspath, dirname, basename

config_file = join(abspath(dirname(__file__)), "fp_config.yml")


@fp.profile(config_file=config_file)
def handler(event, context):
    return {
        "message": "hello_world"
    }
