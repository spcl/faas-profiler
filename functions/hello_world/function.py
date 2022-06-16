#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A AWS Lambda function.
"""

import py_faas_profiler

def handler(event, context):
    return {
        "message": "Hello World",
        "fp_version": py_faas_profiler.__version__
    }