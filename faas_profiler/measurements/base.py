#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base for Measurements.

Defines abstract base class for all measurements and measuring points
"""


from abc import ABC, abstractmethod, abstractproperty
from typing import Any, List, NamedTuple, Type
from schema import Schema


class Measurement(ABC):
    """
    TODO:
    """

    schema: Type[Schema] = None
    name: str = None

    @abstractproperty
    def results(self) -> dict:
        pass

    @abstractmethod
    def on_start(self, pid: int, timestamp: float) -> None:
        pass

    @abstractmethod
    def on_stop(self, pid: int, timestamp: float) -> None:
        pass

    @abstractmethod
    def sample_measure(self, timestamp: float) -> None:
        pass


class MeasuringPoint(NamedTuple):
    timestamp: float
    value: Any

#
#   COMMON MEASUREMENTS
#


class ExecutionTime(Measurement):

    schema = Schema({
        'execution_time': float
    })
    name = "Execution Time"

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def on_start(self, pid, timestamp) -> None:
        self.start_time = timestamp
        self.end_time = 0.0

    def on_stop(self, pid, timestamp) -> None:
        self.end_time = timestamp

    def sample_measure(self, _) -> None:
        pass

    @property
    def results(self) -> dict:
        return self.schema.validate({
            'execution_time': float(self.end_time - self.start_time)
        })
