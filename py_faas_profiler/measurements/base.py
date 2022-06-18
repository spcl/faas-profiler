#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base for Measurements.

Defines abstract base class for all measurements and measuring points
"""
from __future__ import annotations
from ctypes import Union

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


class MeasurementGroup:
    """
    TODO:
    """

    _logger = logging.getLogger("MeasurementGroup")

    @classmethod
    def make_groups(cls, measurement_list: list):
        parallel_meas = []
        base_meas = []

        for measurement in measurement_list:
            meas_name = measurement.get("name")
            if meas_name:
                try:
                    meas_cls = Measurement.factory(meas_name)
                except MeasurementError:
                    return
                    # TODO log this

                if issubclass(meas_cls, ParallelMeasurement):
                    parallel_meas.append(
                        (meas_cls, measurement.get("parameters", {})))
                else:
                    base_meas.append(
                        (meas_cls, measurement.get(
                            "parameters", {})))
            else:
                pass
                # TODO: log this

        return (
            MeasurementGroup(parallel_meas),
            MeasurementGroup(base_meas)
        )

    def __init__(
        self,
        measurements: List[Tuple[Measurement], dict],
    ) -> None:
        self.meas_classes, self.meas_params = zip(*measurements)
        self.meas_instances = []

    def initialize_all(self) -> None:
        """
        Initialize all measurements.
        """
        self.meas_instances = []
        for meas_cls in self.meas_classes:
            try:
                self.meas_instances.append(meas_cls())
            except RuntimeError as err:
                self._logger.error(
                    f"Initializing {meas_cls.name} failed: {err}")

    def setUp_all(self, profile_context: Type[ProfileContext]) -> None:
        """
        Set up all measurements with given parameters.
        """
        for meas, params in zip(self.meas_instances, self.meas_params):
            try:
                meas.setUp(profile_context, params)
            except RuntimeError as err:
                self._logger.error(f"Setting up {meas.name} failed: {err}")

    def start_all(self) -> None:
        """
        Starts all measurements.
        """
        for meas in self.meas_instances:
            try:
                meas.start()
            except RuntimeError as err:
                self._logger.error(f"Starting {meas.name} failed: {err}")

    def measure_all(self):
        """
        Triggers all measuring methods.
        """
        for meas in self.meas_instances:
            try:
                meas.measure()
            except RuntimeError as err:
                self._logger.error(
                    f"Calling measure of {meas.name} failed: {err}")

    def stop_all(self):
        """
        Stops all measurements.
        """
        for meas in self.meas_instances:
            try:
                meas.stop()
            except RuntimeError as err:
                self._logger.error(f"Stopping {meas.name} failed: {err}")


class MeasurementProcess(Process):
    """
    Process to run all measurements that are to be executed in parallel to the main process.
    """

    _logger = logging.getLogger("MeasurementProcess")

    def __init__(
        self,
        measurement_group: Type[MeasurementGroup],
        profile_context: Type[ProfileContext],
        pipe_endpoint: Type[connection.Connection],
        refresh_interval: float = 0.1
    ) -> None:
        self.profile_context = profile_context
        self.pipe_endpoint = pipe_endpoint
        self.refresh_interval = refresh_interval
        self.measurement_group = measurement_group

        self.measurement_group.setUp_all(self.profile_context)

        super(MeasurementProcess, self).__init__()

    def run(self):
        """
        Process routine.

        Starts all measurements first and then generates new measurement points interval-based.
        Stops when the main process tells it to do so.
        Then stops all measurements and sends the results to the main process.
        """
        self._logger.info("Measurement process started.")

        self.measurement_group.start_all()
        self.pipe_endpoint.send(MeasuringState.STARTED)

        self._logger.info("Measurement process started measuring.")

        state = MeasuringState.STARTED
        while state == MeasuringState.STARTED:
            self.measurement_group.measure_all()

            if self.pipe_endpoint.poll(self.refresh_interval):
                state = self.pipe_endpoint.recv()

        self._logger.info("Measurement process stopped measuring.")

        self.measurement_group.stop_all()
        self.pipe_endpoint.send(MeasuringState.STOPPED)
