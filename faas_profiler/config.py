#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join

PACKAGE_ROOT = abspath(dirname(__file__))
TEMPLATES_DIR = join(PACKAGE_ROOT, "templates")

PROJECT_ROOT = abspath(dirname(PACKAGE_ROOT))
EXAMPLES_DIR = join(PROJECT_ROOT, "examples")
