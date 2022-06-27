#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A AWS Lambda function.
"""

import py_faas_profiler as fp

import boto3
from os.path import join, abspath, dirname, basename

config_file = join(abspath(dirname(__file__)), "fp_config.yml")

@fp.profile(config_file=config_file)
def handler(event, context):
    s3 = boto3.client('s3')
    image = join(abspath(dirname(__file__)), "server.jpg")

    key = s3.upload_file(
        image,
        'faas-profiler-resources',
        f"uploades/{basename(image)}")

    return {
        "image_key": key
    }