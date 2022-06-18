#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base for Measurements.

Defines abstract base class for all measurements and measuring points
"""
from __future__ import annotations

import logging

from typing import Dict, List, Tuple, Type
from multiprocessing import Process, connection
from inflection import underscore

from py_faas_profiler.config import ProfileContext, MeasuringState


class MeasurementError(RuntimeError):
    pass


class Measurement:
    """
    Base class for all measurements in FaaS Profiler.

    Cannot be initialised.
    """
    _measurements_: Dict[str, Measurement] = {}

    name: str = ""
    name_parts: tuple = tuple()
    key: str = ""

    #
    # Measurement factory methods
    #

    @classmethod
    def register(cls, name, module_delimiter: str = "::"):
        def decorator(subclass):
            cls._measurements_[name] = subclass
            subclass.name = name
            subclass.name_parts = tuple(underscore(part)
                                        for part in name.split(module_delimiter))
            subclass.key = "_".join(subclass.name_parts)

            return subclass
        return decorator

    @classmethod
    def factory(cls, name):
        try:
            return cls._measurements_[name]
        except KeyError:
            raise MeasurementError(
                f"Unknown measurement name {name}. Available measurements: {list(cls._measurements_.keys())}")

    def setUp(
            self,
            profiler_context: Type[ProfileContext],
            config: dict = {}) -> None:
        """
        TODO
        """
        pass

    def start(self) -> None:
        """
        TODO
        """
        pass

    def stop(self) -> None:
        """
        TODO
        """
        pass

    def tearDown(self) -> None:
        """
        TODO
        """
        pass


class ParallelMeasurement(Measurement):
    """
    Base class for measurements that are executed in parallel in another process.
    """

    def measure(self):
        pass


class MeasurementProcess(Process):
    """
    Process to run all measurements that are to be executed in parallel to the main process.
    """

    _logger = logging.getLogger("MeasurementProcess")

    def __init__(
        self,
        measurements: List[Tuple[ParallelMeasurement], dict],
        profile_context: Type[ProfileContext],
        pipe_endpoint: Type[connection.Connection],
        refresh_interval: float = 0.1
    ) -> None:
        self.profile_context = profile_context
        self.pipe_endpoint = pipe_endpoint
        self.refresh_interval = refresh_interval
        self.measurements = self._init_and_setup_measurements(measurements)

        super(MeasurementProcess, self).__init__()

    def run(self):
        """
        Process routine.

        Starts all measurements first and then generates new measurement points interval-based.
        Stops when the main process tells it to do so.
        Then stops all measurements and sends the results to the main process.
        """
        self._logger.info("Measurement process started.")

        self._start_measurements()
        self.pipe_endpoint.send(MeasuringState.STARTED)

        self._logger.info("Measurement process started measuring.")

        state = MeasuringState.STARTED
        while state == MeasuringState.STARTED:
            self._measure()

            if self.pipe_endpoint.poll(self.refresh_interval):
                state = self.pipe_endpoint.recv()

        self._logger.info("Measurement process stopped measuring.")

        self._stop_measurements()
        self.pipe_endpoint.send(MeasuringState.STOPPED)

    def _init_and_setup_measurements(self,
                                     measurements: List[Tuple[ParallelMeasurement],
                                                        dict]) -> List[Type[ParallelMeasurement]]:
        measurement_instances = []

        for meas_cls, meas_config in measurements:
            try:
                meas_instance = meas_cls()
                meas_instance.setUp(self.profile_context, meas_config)
            except RuntimeError as err:
                self._logger.error(f"Setting up {meas_cls.name} failed: {err}")

        return measurement_instances

    def _start_measurements(self):
        """
        Starts all measurements.

        Does not stop on errors while starting measurements, logs errors only.
        """
        for meas in self.measurements:
            try:
                meas.start()
            except RuntimeError as err:
                self._logger.error(f"Starting {meas.name} failed: {err}")

    def _measure(self):
        """
        Triggers all measuring methods.
        """
        for meas in self.measurements:
            try:
                meas.measure()
            except RuntimeError as err:
                self._logger.error(
                    f"Calling measure of {meas.name} failed: {err}")

    def _stop_measurements(self):
        """
        Stops all measurements.

        Does not stop on errors while stopping measurements, logs errors only.
        """
        for meas in self.measurements:
            try:
                meas.stop()
            except RuntimeError as err:
                self._logger.error(f"Stopping {meas.name} failed: {err}")
