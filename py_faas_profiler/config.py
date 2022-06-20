#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler configuration
"""

from os.path import dirname, join, abspath, exists
from json import load
from enum import Enum
from dataclasses import dataclass
from typing import Any, Type
import uuid

ROOT_DIR = abspath(dirname(__file__))
SHARED_DIR = join(dirname(ROOT_DIR), "shared")
SCHEMAS_DIR = join(SHARED_DIR, "schemas")

# TODO: make case dest for AWS, local usw
TMP_RESULT_DIR = abspath("/tmp")


@dataclass
class ProfileContext:
    """
    Data classes for the context of the current profile run.
    """
    profile_run_id: Type[uuid.UUID]
    profile_run_tmp_dir: str
    pid: int
    measurement_process_pid: int = None


@dataclass
class MeasuringPoint:
    """
    Data class for measuring points during parallel measurements
    """
    timestamp: int
    data: Any


class MeasuringState(Enum):
    STARTED = 1
    STOPPED = 3


def load_schema_by_measurement_name(
    name: str,
    file_ext: str = ".schema.json"
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
