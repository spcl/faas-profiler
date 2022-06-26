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

    a = [1] * (10 ** 6)
    b = [2] * (2 * 10 ** 7)
    del b

    s3 = boto3.client('s3')
    s3.download_file('faas-profiler-resources', 'coffee.jpg', file_name)
    s3.upload_file(
        file_name,
        'faas-profiler-resources',
        f"reloop/{basename(file_name)}")

    f = open(file_name, 'r')
    print(f.name)
    f.close()

    return {
        "message": "foo"
    }


if __name__ == "__main__":
    handler(None, None)
