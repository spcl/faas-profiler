#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base for Measurements.

Defines abstract base class for all measurements and measuring points
"""

from typing import TYPE_CHECKING, Any, List, NamedTuple, Type
from multiprocessing import Process, Pipe, connection

if TYPE_CHECKING:
    from py_faas_profiler.profiler import ProfileContext


class MeasurementError(RuntimeError):
    pass


class Measurement:
    """
    Base class for all measurements in FaaS Profiler.

    Cannot be initialised.
    """
    _measurement_ = None
    _measurements_ = {}

    @classmethod
    def register(cls, name):
        def decorator(subclass):
            cls._measurements_[name] = subclass
            subclass._measurement_ = name
            return subclass
        return decorator

    @classmethod
    def factory(cls, name):
        try:
            return cls._measurements_[name]
        except KeyError:
            raise MeasurementError(
                f"Unknown measurement name {name}. Available measurements: {list(cls._measurements_.keys())}")

    def __init__(self) -> None:
        self._profiler_context: Type[ProfileContext] = None

    def setUp(self):
        pass

    def tearDown(self):
        pass


class ParallelMeasurement(Measurement):
    """
    Base class for measurements that are executed in parallel in another process.
    """

    def measure(self):
        pass
