#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A AWS Lambda function.
"""

from time import sleep
import py_faas_profiler as fp


@fp.profile()
def handler(event, context):
    sleep(3)
    return {
        "message": "hello_world"
    }


if __name__ == "__main__":
    handler(None, None)
