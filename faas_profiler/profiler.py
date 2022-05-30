#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TODO:
"""

from enum import Enum
import os
from time import sleep
from typing import List, Type, Callable, Any
from functools import wraps
from multiprocessing import Process, Pipe, connection

from faas_profiler.measurements import *


def profile(
    measurements=None,
    formatter=None,
    exporters=None
):
    """
    FaaS Profiler decorator.
    Use this decorator to profile a serverless function.
    Parameters
    ----------
    measurements : List[Measurements]
        List of measurement instances
    formatter : Formatter
        Instance of a formatter to be used to format the results
    exporters : List[Exporters]
        List of exporter instances.
    """

    def function_profiler(func):
        @wraps(func)
        def profiler_wrapper(*args, **kwargs):
            profiler = Profiler(formatter, exporters, measurements)

            function_return = profiler(func, *args, **kwargs)

            profiler.export()
            return function_return
        return profiler_wrapper
    return function_profiler


class Profiler:
    """
    FaaS Profiler.
    """

    available_measurements = Measurement.__subclasses__()

    def __init__(
        self,
        measurements: List[Type[Measurement]] = None,
        formatter=None,
        exporters = None
    ) -> None:
        self.measurements = measurements if measurements else self._initialize_all_measurements()
        self.formatter = formatter
        self.exporters = exporters

        if not self.measurements:
            raise RuntimeError("Cannot create a profiler without configured measurements.")

        self.profiler_pid = os.getpid()

        self.profile_process: Type[ProfileProcess] = None
        self.parent_endpoint: Type[connection.Connection] = None
        self.child_endpoint: Type[connection.Connection] = None

        self.results = None

    def start(self) -> None:
        """
        Starts a new profile run.
        """
        # Terminate Process and close pipe if there are defined
        if self.profile_process:
            self.profile_process.terminate()

        if self.parent_endpoint:
            self.parent_endpoint.close()
        
        if self.child_endpoint:
            self.child_endpoint.close()

        # Create new pipes
        self.child_endpoint, self.parent_endpoint = Pipe()
        # Create Profile Process
        self.profile_process = ProfileProcess(
            profile_pid=self.profiler_pid,
            measurements=self.measurements,
            pipe_endpoint=self.child_endpoint)

        # Start Process
        self.profile_process.start()

        process_state = self.parent_endpoint.recv()
        if process_state == ProfilerState.ERROR:
            raise RuntimeError("Error")


    def stop(self) -> None:
        """
        Stops the current profile run.
        """
        self.parent_endpoint.send(ProfilerState.STOPPED)

        process_state = self.parent_endpoint.recv()
        if process_state == ProfilerState.ERROR:
            raise RuntimeError("Error while Stopping")

        self.results =  self.parent_endpoint.recv()
        self.profile_process.join()

    def export(self) -> None:
        """
        Exports the current profile run.
        """
        print(self.results)

    def __call__(self, func: Type[Callable], *args, **kwargs) -> Any:
        """
        Profiles the given method.
        """
        self.start()

        func_ret = func(*args, **kwargs)
        
        self.stop()

        return func_ret

    def _initialize_all_measurements(self) -> List[Type[Measurement]]:
        """
        Initalises all available measurements.
        """
        return [meas() for meas in self.available_measurements]


class ProfilerState(Enum):
    STARTED = 0
    MEASURING = 1
    STOPPED = 2
    ERROR = -1


class ProfileProcess(Process):
    """
    Process to profile the main process parallely.
    """

    def __init__(
        self,
        profile_pid: int,
        pipe_endpoint: Type[connection.Connection],
        measurements: List[Type[Measurement]],
        refresh_interval: float = 0.1
    ) -> None:
        """
        Constructor for new ProfilerProcess.

        Parameters
        ----------
        profile_pid : int
            ID of the process to be profiled.
        pipe_endpoint : Connection
            Pipe endpoint to communicate with the main process.
        measurements : List[Measurement]
            List of measurements to be performed.
        refresh_interval : float
            Refresh interval for polling.
        """
        self.measurements = measurements

        self.profile_pid = profile_pid
        self.pipe_endpoint = pipe_endpoint

        self.refresh_interval = refresh_interval

        super(ProfileProcess, self).__init__()

    def run(self) -> None:
        """
        Process routine.

        Starts all measurements first and then generates new measurement points interval-based.
        Stops when the main process tells it to do so.
        Then stops all measurements and sends the results to the main process.
        """
        # Start Measurements
        if self._start_measurements():
            self.pipe_endpoint.send(ProfilerState.STARTED)
        else:
            self.pipe_endpoint.send(ProfilerState.ERROR)
            return

        # Trigger measurements functions
        state = ProfilerState.MEASURING
        while state == ProfilerState.MEASURING:
            # Add new sample:
            sample_timestamp = time()
            for measurement in self.measurements:
                measurement.sample_measure(sample_timestamp)

            if self.pipe_endpoint.poll(self.refresh_interval):
                state = self.pipe_endpoint.recv()

        # Stop results
        if self._stop_measurements():
            self.pipe_endpoint.send(ProfilerState.STOPPED)
        else:
            self.pipe_endpoint.send(ProfilerState.ERROR)
            return


        # Send results
        self.pipe_endpoint.send(self._gather_results())


    def _start_measurements(self) -> bool:
        """
        Starts all measurements.

        Returns True if all measurements started successfully.
        """
        for measurement in self.measurements:
            measurement.on_start(self.profile_pid, time())

        return True

    def _stop_measurements(self) -> bool:
        """
        Stops all measurements.

        Returns True if all measurements stopped successfully.
        """
        for measurement in self.measurements:
            measurement.on_stop(self.profile_pid, time())

        return True


    def _gather_results(self) -> dict:
        """
        Collects all the results of the measurements.
        """
        return {
            meas.name: meas.results for meas in self.measurements
        }