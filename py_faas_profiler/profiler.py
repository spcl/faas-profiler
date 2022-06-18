#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TODO:
"""

import logging
import warnings

from typing import List, Type, Callable, Any
from multiprocessing import Pipe, connection
from functools import wraps
from os import getpid

from py_faas_profiler.measurements import Measurement, MeasurementProcess
from py_faas_profiler.config import ProfileContext, MeasuringState


def profile(config: str = None):
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
            profiler = Profiler(config_file=config)

            function_return = profiler(func, *args, **kwargs)

            return function_return
        return profiler_wrapper
    return function_profiler


class Profiler:

    _logger = logging.getLogger("Profiler")

    def __init__(self, config_file) -> None:
        self.config_file = config_file

        self.profile_context = ProfileContext(pid=getpid())

        self.measurement_process: Type[MeasurementProcess] = None
        self.parent_endpoint: Type[connection.Connection] = None
        self.child_endpoint: Type[connection.Connection] = None

        self.bar = [
            (Measurement.factory("Common::ExecutionTime"), {"foo": 12})
        ]

        self._logger.info(f"Created new Profiler: {self.profile_context}")

    def __call__(self, func: Type[Callable], *args, **kwargs) -> Any:
        """
        Convenience wrapper to profile the given method.
        Profiles the given method and exports the results.
        """
        self._update_profile_context()

        self.start()
        try:
            self._logger.info(f"-- EXECUTING FUNCTION: {func.__name__} --")
            func_ret = func(*args, **kwargs)
            self._logger.info(f"-- FUNCTION EXCUTED --")
        except Exception as ex:
            self._logger.error(f"Function not successfully executed: {ex}")
            warnings.warn(ex)

            func_ret = None
        finally:
            self.stop()

        self.export()

        return func_ret

    def start(self):
        """
        Starts the profiling.
        """
        self._logger.info(f"Starting Profiler...")

        self._terminate_measuring_process()
        self._start_measuring_process()

    def stop(self):
        """
        Stops the profiling.
        """
        self._logger.info("Stopping Profiler...")
        self._stop_measuring_process()
        self._terminate_measuring_process()

    def export(self):
        """
        Exports the profiling data.
        """
        pass

    # Private methods

    def _update_profile_context(self):
        """
        Updates the Profile Context based on the passing arguments.
        """
        # TODO: IMPLEMENT ME

    def _start_measuring_process(self):
        """
        TODO:
        """
        # Set up new pipes and process
        self._logger.info(f"Creating Measuring process for: {self.bar}")
        self.child_endpoint, self.parent_endpoint = Pipe()
        self.measurement_process = MeasurementProcess(
            measurements=self.bar,
            profile_context=self.profile_context,
            pipe_endpoint=self.child_endpoint)

        # Start process
        self._logger.info(
            f"Starting Measuring process for: {self.measurement_process}")
        self.measurement_process.start()

        # Wait until all measurements in the process have started
        self._logger.info("Wait until all parallel measurements started.")
        self.parent_endpoint.recv()

    def _stop_measuring_process(self):
        """
        TODO:
        """
        self._logger.info("Wait until all parallel measurements stopped.")
        self.parent_endpoint.send(MeasuringState.STOPPED)
        self.parent_endpoint.recv()

        self._logger.info("Wait Measuring process stopped.")
        self.measurement_process.join()

    def _terminate_measuring_process(self):
        """
        TODO:
        """
        if self.measurement_process:
            self._logger.info(
                f"Terminated Measuring process: {self.measurement_process}")
            self.measurement_process.terminate()

        if self.parent_endpoint:
            self._logger.info(f"Closed parent pipe: {self.parent_endpoint}")
            self.parent_endpoint.close()

        if self.child_endpoint:
            self._logger.info(f"Closed child pipe: {self.child_endpoint}")
            self.child_endpoint.close()
