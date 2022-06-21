#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler configuration
"""
from __future__ import annotations

import logging
import pkg_resources
import yaml

from os import getpid, mkdir
from os.path import dirname, join, abspath, exists
from uuid import uuid4
from json import load
from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Type
from functools import reduce, cached_property
from collections import namedtuple


ROOT_DIR = abspath(dirname(__file__))
SHARED_DIR = join(dirname(ROOT_DIR), "shared")
SCHEMAS_DIR = join(SHARED_DIR, "schemas")

# TODO: make case dest for AWS, local usw
TMP_RESULT_DIR = abspath("/tmp")


def get_faas_profiler_version():
    try:
        return pkg_resources.get_distribution("py_faas_profiler").version
    except pkg_resources.DistributionNotFound:
        return "-"


class Config:

    ConfigItem = namedtuple('ConfigItem', ['name', 'parameters'])

    _logger = logging.getLogger("Config")
    _logger.setLevel(logging.INFO)

    MEASUREMENTS_KEY = "measurements"
    CAPTURES_KEY = "captures"
    EXPORTERS_KEY = "exporters"

    @classmethod
    def load_from_file(cls, config_file: str) -> Type[Config]:
        if exists(config_file):
            try:
                with open(config_file, "r") as fp:
                    try:
                        config = yaml.safe_load(fp)
                        if isinstance(config, dict):
                            return Config(
                                config=config,
                                config_file=config_file)

                        raise ValueError(
                            f"Profiler configuration {config_file} must be a dict, but got {type(config)}")
                    except yaml.YAMLError as err:
                        cls._logger.error(
                            "Could not parse profiler config file: {err}")
            except IOError as err:
                cls._logger.error("Could not open profiler config file: {err}")

        return Config()

    def __init__(
        self,
        config: dict = {},
        config_file: str = None
    ) -> None:
        self._config = config
        self._config_file = config_file

    @cached_property
    def measurements(self):
        return self._parse_to_config_items(
            self._config.get(self.MEASUREMENTS_KEY, []))

    @cached_property
    def exporters(self) -> List[Config.ConfigItem]:
        return self._parse_to_config_items(
            self._config.get(self.EXPORTERS_KEY, []))

    @cached_property
    def captures(self) -> List[Config.ConfigItem]:
        return self._parse_to_config_items(
            self._config.get(self.CAPTURES_KEY, []))

    def _parse_to_config_items(
        self,
        config_list: list
    ) -> List[Config.ConfigItem]:
        if not config_list:
            return []

        items = []
        for config in config_list:
            name = config.get("name")
            if name:
                items.append(Config.ConfigItem(
                    name, config.get("parameters", {})))

        return items


class ProfileContext:
    """
    TODO:
    """

    def __init__(self) -> None:
        self._profile_run_id = uuid4()
        self._pid: int = getpid()
        self._measurement_process_pid: int = None
        self._tmp_dir = join(TMP_RESULT_DIR,
                             f"faas_profiler_{self.profile_run_id}_results")

        mkdir(self._tmp_dir)

    def set_measurement_process_pid(self, pid: int) -> None:
        self._measurement_process_pid = pid

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def measurement_process_pid(self):
        return self._measurement_process_pid

    @property
    def profile_run_id(self):
        return self._profile_run_id

    @property
    def tmp_results_dir(self):
        return self._tmp_dir


@dataclass
class MeasuringPoint:
    """
    Data class for measuring points during parallel measurements
    """
    timestamp: int
    data: Any


def average_measuring_points(points: List[MeasuringPoint]) -> Any:
    """
    Calculates the average value of a list of measurement points,
    with the assumption that the "data" property is addable.
    """
    return reduce(
        lambda total, point: total + point.data,
        points,
        0) / len(points)


class MeasuringState(Enum):
    STARTED = 1
    STOPPED = 2
    ERROR = -1


@dataclass
class ProcessFeedback:
    state: MeasuringState
    data: Any = None


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
