#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler configuration
"""

from os.path import dirname, join, abspath, exists
from json import load
from enum import Enum
from dataclasses import dataclass

ROOT_DIR = abspath(dirname(__file__))
SHARED_DIR = join(dirname(ROOT_DIR), "shared")
SCHEMAS_DIR = join(SHARED_DIR, "schemas")


@dataclass
class ProfileContext:
    """
    Data classes for the context of the current profile run.
    """
    pid: int


class MeasuringState(Enum):
    STARTED = 1
    STOPPED = 3


def load_schema_by_measurement_name(
    name: str,
    file_ext: str = ".schema"
) -> dict:
    """
    Loads a measurement result scheme for the given measurement names.
    """
    schema_file = join(SCHEMAS_DIR, *name) + file_ext
    if exists(schema_file):
        with open(schema_file, "r") as fh:
            try:
                return load(fh)
            except ValueError:
                # TODO: Log that file is not json loadable
                return {}
    else:
        # TODO: Log that file not found
        return {}
