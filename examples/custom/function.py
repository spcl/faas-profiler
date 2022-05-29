#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Lambda Function
"""

import faas_profiler as fp

@fp.profile()
def handler(event, context):
    a = [1] * (10 ** 6)
    b = [2] * (2 * 10 ** 7)
    del b
    return a


if __name__ == "__main__":
    handler(None, None)