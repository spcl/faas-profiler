#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Lambda Function
"""

from datetime import datetime
from os import path, environ

import boto3

import faas_profiler as fp
from faas_profiler.captures import InvocationCapture
from faas_profiler.export import S3Exporter


def write_ethz_to_file(file):
    from urllib.request import Request, urlopen
    req = Request(
        'https://www.ethz.ch/',
        headers={
            'User-Agent': 'Mozilla/5.0'})
    connection = urlopen(req)

    with open(file, "w") as f:
        f.write(connection.read().decode("utf-8"))


def some_memory_heavy_calc():
    a = [1] * (10 ** 6)
    b = [2] * (2 * 10 ** 7)

    del b
    return a


def write_some_content(file, content):
    with open(file, "w") as f:
        f.write(str(content))


def upload_s3():
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file("foo", "bar", "barz")
    except Exception as e:
        print("mhm")


@fp.profile(
    exporters=[
        S3Exporter(
            environ['BUCKET_NAME'],
            "results")],
    invocation_capture=InvocationCapture(
        ["boto3.s3.transfer.S3Transfer.upload_file"]))
def handler(event, context):
    temp_dir = "/tmp/"
    file_suffix = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    content = some_memory_heavy_calc()

    write_ethz_to_file(path.join(temp_dir, f"ethz_{file_suffix}.html"))

    write_some_content(
        path.join(
            temp_dir,
            f"foo_{file_suffix}.text"),
        content)

    upload_s3()


if __name__ == "__main__":
    handler(None, None)
