#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base for Measurements.

Defines abstract base class for all measurements and measuring points
"""

from __future__ import annotations

import json
import logging
import os
import warnings
import traceback

from os.path import join
from typing import List, Tuple, Type
from multiprocessing import Process, connection
from jsonschema import validate, ValidationError

from py_faas_profiler.utilis import Registerable
from py_faas_profiler.config import (
    Config,
    ProfileContext,
    MeasuringState,
    ProcessFeedback,
    load_schema_by_measurement_name
)


class MeasurementError(RuntimeError):
    pass


class Measurement(Registerable):
    """
    Base class for all measurements in FaaS Profiler.

    Cannot be initialised.
    """

    def __init__(
        self,
        profiler_context: Type[ProfileContext],
    ) -> None:
        self.results_schema = load_schema_by_measurement_name(self.name_parts)
        self.tmp_results_file = join(
            profiler_context.tmp_results_dir,
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

        try:
            with open(self.tmp_results_file, 'w+') as fh:
                json.dump(results, fh)
        except IOError as err:
            raise MeasurementError(
                f"I/O error during exporting {self.name}: {err}")
        except BaseException as err:
            raise MeasurementError(
                f"Unexpected error during exporting {self.name}: {err}")


class PeriodicMeasurement(Measurement):
    """
    Base class for measurements that are executed in parallel in another process.
    """

    def measure(self):
        pass


register_with_name = Measurement.register


class MeasurementGroup:
    """
    TODO:
    """

    _logger = logging.getLogger("MeasurementGroup")
    _logger.setLevel(logging.INFO)

    @classmethod
    def make_groups(cls, measurement_list: List[Type[Config.ConfigItem]]):
        periodics = []
        defaults = []

        for measurement in measurement_list:
            try:
                klass = Measurement.factory(measurement.name)
            except ValueError:
                cls._logger.warn(
                    f"Skipping {measurement.name}. No measurement found for given name.")
            else:
                if issubclass(klass, PeriodicMeasurement):
                    periodics.append((klass, measurement.parameters))
                else:
                    defaults.append((klass, measurement.parameters))

        return (
            MeasurementGroup(*defaults),
            MeasurementGroup(*periodics))

    def __init__(
        self,
        *measurements: List[Tuple[Measurement], dict],
    ) -> None:
        self.measurements = measurements
        self.instances = []

    def setUp_all(self, profile_context: Type[ProfileContext]) -> None:
        """
        Set up all measurements with given parameters.
        """
        if not self.measurements:
            return

        self.instances = []
        for meas_cls, meas_params in self.measurements:
            meas = meas_cls(profile_context)
            meas.setUp(profile_context, meas_params)

            self.instances.append(meas)

    def start_all(self) -> None:
        """
        Starts all measurements.
        """
        for meas in self.instances:
            meas.start()

    def measure_all(self):
        """
        Triggers all measuring methods.
        """
        for meas in self.instances:
            meas.measure()

    def stop_all(self):
        """
        Stops all measurements.
        """
        for meas in self.instances:
            meas.stop()

    def tearDown_all(self):
        """
        Tears down all measurements.
        """
        for meas in self.instances:
            meas.tearDown()
            meas.write_results()


class MeasurementProcessError(RuntimeError):
    pass


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
        parent_connection: Type[connection.Connection],
        child_connection: Type[connection.Connection],
        refresh_interval: float = 0.1
    ) -> None:
        self.profile_context = profile_context
        self.parent_connection = parent_connection
        self.child_connection = child_connection
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
        try:
            measurement_process_pid = os.getpid()
            self._logger.info(
                f"Measurement process started (pid={measurement_process_pid}).")
            self.profile_context.set_measurement_process_pid(
                measurement_process_pid)

            self.measurement_group.setUp_all(self.profile_context)
            self.measurement_group.start_all()
            self.child_connection.send(ProcessFeedback(MeasuringState.STARTED))

            self._logger.info("Measurement process started measuring.")

            state = MeasuringState.STARTED
            while state == MeasuringState.STARTED:
                self.measurement_group.measure_all()

                if self.child_connection.poll(self.refresh_interval):
                    state = self.child_connection.recv()

            self._logger.info("Measurement process stopped measuring.")

            self.measurement_group.stop_all()
            self.child_connection.send(ProcessFeedback(MeasuringState.STOPPED))

            self.measurement_group.tearDown_all()
        except Exception as e:
            tb = traceback.format_exc()
            self.child_connection.send(ProcessFeedback(
                state=MeasuringState.ERROR,
                data=(e, tb)
            ))

    def wait_for_state(self, state: MeasuringState, timeout: int = 10):
        if self.parent_connection.poll(timeout):
            feedback = self.parent_connection.recv()
            if feedback.state == state:
                return True
            elif feedback.state == MeasuringState.ERROR:
                error, tb = feedback.data
                print(tb)
                raise error
