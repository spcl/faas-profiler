#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TODO:
"""

import logging
import traceback

from typing import List, Type, Callable, Any
from multiprocessing import Pipe, connection
from functools import wraps

from py_faas_profiler.captures.base import Capture
from py_faas_profiler.measurements import MeasurementProcess, MeasurementGroup
from py_faas_profiler.config import Config, ProfileContext, MeasuringState
from py_faas_profiler.exporter import ResultsCollector, Exporter
from py_faas_profiler.patchers import unpatch_modules


def profile(config_file: str = None):
    """
    FaaS Profiler decorator.
    Use this decorator to profile a serverless function.

    Parameters
    ----------
    config : str
        Path to configuration file.
    """

    def function_profiler(func):
        @wraps(func)
        def profiler_wrapper(*args, **kwargs):
            profiler = Profiler(config_file=config_file)

            function_return = profiler(func, *args, **kwargs)

            return function_return
        return profiler_wrapper
    return function_profiler


class Profiler:

    _logger = logging.getLogger("Profiler")
    _logger.setLevel(logging.INFO)

    def __init__(self, config_file: str = None) -> None:
        self._logger.info(f"Load configuration: {config_file}")
        self.config = Config.load_from_file(config_file)

        # Profiler Context
        self.profile_context = ProfileContext()

        # Measurements
        self.default_measurements: Type[MeasurementGroup] = None
        self.periodic_measurements: Type[MeasurementGroup] = None

        self._default_measurements_started: bool = False
        self._periodic_measurements_started: bool = False

        self._make_measurement_groups()

        print(self.default_measurements.measurements)

        # Captures
        self.active_captures: List[Type[Capture]] = []

        # Measurement process for peridic measurements
        self.child_endpoint: Type[connection.Connection] = None
        self.parent_endpoint: Type[connection.Connection] = None
        self.measurement_process: Type[MeasurementProcess] = None

        self._logger.info((
            "[PROFILER PLAN]: \n"
            f"- Measurements: {self.config.measurements} \n"
            f"- Captures: {self.config.captures} \n"
            f"- Exporters: {self.config.exporters}"
        ))

    def __call__(self, func: Type[Callable], *args, **kwargs) -> Any:
        """
        Convenience wrapper to profile the given method.
        Profiles the given method and exports the results.
        """

        self.start()
        self._logger.info(f"-- EXECUTING FUNCTION: {func.__name__} --")
        try:
            func_ret = func(*args, **kwargs)
        except Exception as ex:
            self._logger.error(f"Function not successfully executed: {ex}")

            func_ret = None
        finally:
            self._logger.info(f"-- FUNCTION EXCUTED --")
            self.stop()

        self.export()

        return func_ret

    def start(self):
        """
        Starts the profiling.
        """
        self._logger.info("Profiler run started.")
        self._start_capturing_and_tracing()
        self._start_default_measurements()
        self._start_periodic_measurements()

    def stop(self):
        """
        Stops the profiling.
        """
        self._logger.info("Profile run stopped.")
        self._stop_periodic_measurements()
        self._stop_default_measurements()
        self._stop_capturing_and_tracing()

        if self.measurement_process:
            self.measurement_process.join()
            self._terminate_measuring_process()

    def export(self):
        """
        Exports the profiling data.
        """
        if not self.config.exporters:
            self._logger.warn("No exporters defined. Will discard results.")
            return

        results_collector = ResultsCollector(
            config=self.config,
            profile_context=self.profile_context,
            captures=self.active_captures)

        for config_item in self.config.exporters:
            try:
                exporter = Exporter.factory(config_item.name)
            except ValueError:
                self._logger.error(
                    f"No exporter found with name {config_item.name}")
                continue

            exporter(
                self.profile_context,
                config_item.parameters).dump(results_collector)

    # Private methods

    def _make_measurement_groups(self):
        self.default_measurements, self.periodic_measurements = MeasurementGroup.make_groups(
            measurement_list=self.config.measurements)

    def _start_default_measurements(self):
        if not self.default_measurements:
            return

        try:
            self.default_measurements.setUp_all(self.profile_context)
            self.default_measurements.start_all()
            self._default_measurements_started = True

            self._logger.info(
                "[DEFAULT MEASUREMENTS]: All set up and started.")
        except Exception as err:
            self._default_measurements_started = False

            self._logger.error(
                f"[DEFAULT MEASUREMENTS]: Initializing/Setting up failed: {err}, Traceback: {traceback.format_exc()}")

    def _start_periodic_measurements(self):
        if not self.periodic_measurements:
            return

        self.child_endpoint, self.parent_endpoint = Pipe()
        self.measurement_process = MeasurementProcess(
            measurement_group=self.periodic_measurements,
            profile_context=self.profile_context,
            child_connection=self.child_endpoint,
            parent_connection=self.parent_endpoint)

        self._logger.info(
            f"[PERIODIC MEASUREMENT]: Starting process: {self.measurement_process}")
        self.measurement_process.start()

        try:
            self.measurement_process.wait_for_state(MeasuringState.STARTED)
            self._periodic_measurements_started = True

            self._logger.info(
                "[PERIODIC MEASUREMENT]: All set up and started.")
        except Exception as err:
            self._terminate_measuring_process()
            self._periodic_measurements_started = False

            self._logger.error(
                f"[PERIODIC MEASUREMENT]: Initializing/Setting up failed: {err}")

    def _stop_default_measurements(self):
        if not self.default_measurements:
            return

        if not self._default_measurements_started:
            self._logger.warn(
                "[DEFAULT MEASUREMENTS]: Attempts to stop measurements before they are successfully started. Skipping.")
            return

        try:
            self.default_measurements.stop_all()
            self.default_measurements.tearDown_all()
            self._logger.info(
                "[DEFAULT MEASUREMENTS]: All stopped and terminated")
        except Exception as err:
            self._logger.error(
                f"[DEFAULT MEASUREMENTS]: Stopping and shutting down failed: {err}, Traceback: {traceback.format_exc()}")

    def _stop_periodic_measurements(self):
        if not self.measurement_process:
            return

        if not self._periodic_measurements_started:
            self._logger.warn(
                "[PERIODIC MEASUREMENTS]: Attempts to stop measurements before they are successfully started. Skipping.")
            return

        # Send child process request to stop
        self.parent_endpoint.send(MeasuringState.STOPPED)

        try:
            self.measurement_process.wait_for_state(MeasuringState.STOPPED)
            self._logger.info(
                "[PERIODIC MEASUREMENT]: All stopped and terminated")
        except Exception as err:
            self._logger.error(
                f"[DEFAULT MEASUREMENTS]: Stopping and shutting down failed: {err}")

    def _terminate_measuring_process(self):
        """
        TODO:
        """
        if self.measurement_process and self.measurement_process.is_alive():
            self._logger.info(
                f"Terminated Measuring process: {self.measurement_process}")
            self.measurement_process.terminate()

        if self.parent_endpoint and not self.parent_endpoint.closed:
            self._logger.info(f"Closed parent pipe: {self.parent_endpoint}")
            self.parent_endpoint.close()

        if self.child_endpoint and not self.parent_endpoint.closed:
            self._logger.info(f"Closed child pipe: {self.child_endpoint}")
            self.child_endpoint.close()

    def _start_capturing_and_tracing(self):
        for capture_conf in self.config.captures:
            try:
                capture_class = Capture.factory(capture_conf.name)
            except ValueError:
                self._logger.warn(
                    f"[CAPTURES]: Could not find a capture with name: {capture_conf.name}")
            else:
                capture = capture_class(capture_conf.parameters)
                capture.start()

                self.active_captures.append(capture)
        self._logger.info("[CAPTURES]: Started all captures")

    def _stop_capturing_and_tracing(self):
        for patcher in self.active_captures:
            patcher.stop()
        self._logger.info("[CAPTURES]: Stopped all captures")

        unpatch_modules()
        self._logger.info("[CAPTURES]: Unpatched all modules.")
