#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A AWS Lambda function.
"""

import py_faas_profiler as fp

import boto3
from random import randint
from os.path import join, abspath, dirname, basename

config_file = join(abspath(dirname(__file__)), "fp_config.yml")


@fp.profile(config_file=config_file)
def handler(event, context):
    file_name = f'/tmp/coffee_{randint(0, 100)}.jpg'

    s3 = boto3.client('s3')
    s3.download_file('faas-profiler-resources', 'coffee.jpg', file_name)
    s3.upload_file(
        file_name,
        'faas-profiler-resources',
        f"reloop/{basename(file_name)}")

    return {
        "message": "hello_world"
    }


if __name__ == "__main__":
    handler(None, None)
