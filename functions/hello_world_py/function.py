#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A AWS Lambda function.
"""

import py_faas_profiler as fp

@fp.profile()
def handler(event, context):
    return {
        "message": "hello_world"
    }