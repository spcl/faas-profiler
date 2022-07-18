#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
from os.path import abspath, dirname, join

PACKAGE_ROOT = abspath(dirname(__file__))
TEMPLATES_DIR = join(PACKAGE_ROOT, "templates")

PROJECT_ROOT = abspath(dirname(PACKAGE_ROOT))
EXAMPLES_DIR = join(PROJECT_ROOT, "examples")


class Runtime(Enum):
    UNKNOWN = "unknown"
    PYTHON = "python3.8"
    NODE = "node16.4"


class Provider(Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
