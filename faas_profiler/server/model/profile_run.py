#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Type
from marshmallow import Schema, fields

from ..storage import get_all_results, get_result_by_id
from .measurements import *


class ProfileRun:

    @classmethod
    def find_all(cls) -> List[Type[ProfileRun]]:
        profile_runs = []
        for result in get_all_results():
            profile_runs.append(
                cls(**ProfileRunSchema().load(result)))

        return profile_runs

    @classmethod
    def find(cls, profile_run_id: str) -> Type[ProfileRun]:
        return cls(**ProfileRunSchema().load(
            get_result_by_id(profile_run_id)))

    def __init__(
        self,
        profile_run_id,
        py_faas_version,
        measurements: dict,
    ) -> None:
        self.profile_run_id = profile_run_id
        self.py_faas_version = py_faas_version

        self.measurements = measurements


class ProfileRunSchema(Schema):
    profile_run_id = fields.Str()
    py_faas_version = fields.Str()
    measurements = fields.Dict(
        common_wall_time=fields.Nested(CommonWallTimeSchema, missing=None),
        information_environment=fields.Nested(InformationEnvironmentSchema, missing=None),
        information_operating_system=fields.Nested(InformationOperatingSystemSchema, missing=None),
        memory_usage=fields.Nested(MemoryUsageSchema, missing=None),
        cpu_usage=fields.Nested(CPUUsage, missing=None),
        network_connections=fields.Nested(NetworkConnections, missing=None),
        network_io_counters=fields.Nested(NetworkIOCounters, missing=None)
    )
