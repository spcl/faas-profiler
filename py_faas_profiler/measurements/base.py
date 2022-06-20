#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base for Measurements.

Defines abstract base class for all measurements and measuring points
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import json

import logging
from unittest import result
import warnings

from os.path import join
from typing import Dict, List, Tuple, Type
from multiprocessing import Process, connection
from inflection import underscore
from jsonschema import validate, ValidationError

from py_faas_profiler.config import ProfileContext, MeasuringState, load_schema_by_measurement_name


class MeasurementError(RuntimeError):
    pass


class Measurement(ABC):
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
    def register_with_name(cls, name, module_delimiter: str = "::"):
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

    def __init__(
        self,
        profiler_context: Type[ProfileContext],
    ) -> None:
        self.results_schema = load_schema_by_measurement_name(self.name_parts)
        self.tmp_results_file = join(
            profiler_context.profile_run_tmp_dir,
            f"{self.key}.json")

    def setUp(
        self,
        profiler_context: Type[ProfileContext],
        config: dict = {}
    ) -> None:
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

    @abstractmethod
    def results(self) -> dict:
        return {}

    def write_results(self, export_invalid=False) -> bool:
        results = self.results()
        try:
            validate(instance=results, schema=self.results_schema)
        except ValidationError as err:
            _msg = f"Validation results of {self.name} failed: {err}"
            if not export_invalid:
                raise MeasurementError(_msg)

            warnings.warn(_msg, category=RuntimeWarning)

        print(f"Dump: {results}")
        try:
            with open(self.tmp_results_file, 'w+') as fh:
                json.dump(results, fh)
        except IOError as err:
            raise MeasurementError(
                f"I/O error during exporting {self.name}: {err}")
        except BaseException:
            raise MeasurementError(
                f"Unexpected error during exporting {self.name}: {err}")


class ParallelMeasurement(Measurement):
    """
    Base class for measurements that are executed in parallel in another process.
    """

    def measure(self):
        pass


register_with_name = Measurement.register_with_name


class MeasurementGroup:
    """
    TODO:
    """

    _logger = logging.getLogger("MeasurementGroup")
    _logger.setLevel(logging.INFO)

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
                    continue
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
        self.measurements = measurements
        self.meas_instances = []

    def setUp_all(self, profile_context: Type[ProfileContext]) -> None:
        """
        Set up all measurements with given parameters.
        """
        if not self.measurements:
            return

        self.meas_instances = []
        for meas_cls, meas_params in self.measurements:
            try:
                meas = meas_cls(profile_context)
                meas.setUp(profile_context, meas_params)

                self.meas_instances.append(meas)
            except RuntimeError as err:
                self._logger.error(
                    f"Initializing/Setting up {meas_cls.name} failed: {err}")

    def start_all(self) -> None:
        """
        Starts all measurements.
        """
        for meas in self.meas_instances:
            try:
                meas.start()
            except Exception as err:
                self._logger.error(f"Starting {meas.name} failed: {err}")

    def measure_all(self):
        """
        Triggers all measuring methods.
        """
        for meas in self.meas_instances:
            try:
                meas.measure()
            except Exception as err:
                self._logger.error(
                    f"Calling measure of {meas.name} failed: {err}")

    def stop_all(self):
        """
        Stops all measurements.
        """
        for meas in self.meas_instances:
            try:
                meas.stop()
            except Exception as err:
                self._logger.error(f"Stopping {meas.name} failed: {err}")

    def tearDown_all(self):
        """
        Tears down all measurements.
        """
        for meas in self.meas_instances:
            try:
                meas.tearDown()
                meas.write_results()
            except Exception as err:
                self._logger.error(f"Tearing down {meas.name} failed: {err}")


class MeasurementProcess(Process):
    """
    Process to run all measurements that are to be executed in parallel to the main process.
    """

    _logger = logging.getLogger("MeasurementProcess")
    _logger.setLevel(logging.INFO)

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

        super(MeasurementProcess, self).__init__()

    def run(self):
        """
        Process routine.

        Starts all measurements first and then generates new measurement points interval-based.
        Stops when the main process tells it to do so.
        Then stops all measurements and sends the results to the main process.
        """
        self._logger.info("Measurement process started.")

        self.measurement_group.setUp_all(self.profile_context)
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

        self.measurement_group.tearDown_all()
