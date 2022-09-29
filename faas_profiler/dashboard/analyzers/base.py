#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyzer Base class
"""

from abc import ABC
from enum import Enum
from typing import Dict, Type
from uuid import UUID
from faas_profiler.utilis import Loggable

from faas_profiler_core.models import RecordData


class Dimension(Enum):
    PROFILE = "profile"
    TRACE = "trace"
    RECORD = "record"


class Analyzer(ABC, Loggable):
    requested_data: str = None
    name: str = None

    @classmethod
    def safe_name(cls) -> str:
        """
        Get name or class name
        """
        if cls.name:
            return cls.name

        return cls.__name__()

    def __init__(self):
        super().__init__()

    def analyze_profile(self, traces_data: Dict[UUID, Type[RecordData]]):
        raise NotImplementedError

    def analyze_trace(
        self,
        record_data: Dict[str, Type[RecordData]]
    ):
        raise NotImplementedError

    def analyze_record(self, record_data: Type[RecordData]):
        raise NotImplementedError
