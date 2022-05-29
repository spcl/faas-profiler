#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler Setup Routine
"""
import setuptools

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

setuptools.setup(
    name="faas_profiler",
    description="FaaS-Profiler is a software to profile serverless functions.",
    url="https://github.com/spcl/faas-profiler",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    include_package_data=True
)