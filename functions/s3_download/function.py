#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A AWS Lambda function.
"""

import py_faas_profiler as fp

from os.path import join, abspath, dirname, basename
import boto3

config_file = join(abspath(dirname(__file__)), "fp_config.yml")


@fp.profile(config_file=config_file)
def handler(event, context):
    file_name = f'/tmp/coffee.jpg'

    s3 = boto3.client('s3')
    key = s3.download_file('faas-profiler-resources', 'coffee.jpg', file_name)

    return {
        "key": key
    }
