#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TODO:
"""

import logging
import uuid
import warnings
import yaml

from typing import Type, Callable, Any
from multiprocessing import Pipe
from functools import wraps
from os import getpid, mkdir, path

from py_faas_profiler.measurements.base import MeasurementError
from py_faas_profiler.measurements import MeasurementProcess, MeasurementGroup
from py_faas_profiler.config import ProfileContext, MeasuringState, TMP_RESULT_DIR


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
        self.measurement_config, self.patcher_config, self.exporter_config = self._load_configuration(
            config_file)

        self.parallel_group, self.base_group = MeasurementGroup.make_groups(
            self.measurement_config)

        self.profile_run_id = uuid.uuid4()
        self.profile_run_tmp_dir = path.join(
            TMP_RESULT_DIR, f"faas_profiler_{self.profile_run_id}_results")

        self.profile_context = ProfileContext(
            profile_run_id=self.profile_run_id,
            profile_run_tmp_dir=self.profile_run_tmp_dir,
            pid=getpid())

        self.base_group.setUp_all(self.profile_context)

        # Set up new pipes and process
        self.child_endpoint, self.parent_endpoint = Pipe()
        self.measurement_process = MeasurementProcess(
            measurement_group=self.parallel_group,
            profile_context=self.profile_context,
            pipe_endpoint=self.child_endpoint)

    def __call__(self, func: Type[Callable], *args, **kwargs) -> Any:
        """
        Convenience wrapper to profile the given method.
        Profiles the given method and exports the results.
        """
        self._make_tmp_result_dir()
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

        self._logger.info(f"Starting all measurements in main process.")
        self.base_group.start_all()

        self._start_measuring_process()

    def stop(self):
        """
        Stops the profiling.
        """
        self._logger.info("Stopping Profiler...")
        self._stop_measuring_process()

        self._logger.info(f"Stopping all measurements in main process.")
        self.base_group.stop_all()

        self.base_group.tearDown_all()

        self._logger.info("Wait Measuring process stopped.")
        self.measurement_process.join()

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
        self.profile_context

    def _make_tmp_result_dir(self):
        """
        Creates a temporary folder for results.
        """
        try:
            mkdir(self.profile_run_tmp_dir)
        except OSError as err:
            raise MeasurementError(
                f"Could not create temporary results dir: {err}")

    def _start_measuring_process(self):
        """
        TODO:
        """
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

    def _terminate_measuring_process(self):
        """
        TODO:
        """
        if self.measurement_process and self.measurement_process.is_alive():
            self._logger.info(
                f"Terminated Measuring process: {self.measurement_process}")
            self.measurement_process.terminate()

        if self.parent_endpoint:
            self._logger.info(f"Closed parent pipe: {self.parent_endpoint}")
            self.parent_endpoint.close()

        if self.child_endpoint:
            self._logger.info(f"Closed child pipe: {self.child_endpoint}")
            self.child_endpoint.close()

    def _load_configuration(self, config_file_path: str = None) -> dict:
        if config_file_path is None:
            # TODO: Load default
            return {}, {}, {}

        with open(config_file_path, 'r') as fh:
            all_config = yaml.safe_load(fh)

            return (
                all_config.get("measurements"),
                all_config.get("patchers"),
                all_config.get("exporters"))
