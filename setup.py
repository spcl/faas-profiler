#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler CLI setup routine.
"""

import setuptools

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

setuptools.setup(
    name='faas-profiler',
    version='0.0.1',
    url='https://github.com/spcl/faas-profiler',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'fp = faas_profiler.__main__:main'
        ],
    },
)