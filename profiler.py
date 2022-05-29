#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TODO:
"""

from typing import List, Type, Callable, Any
from functools import wraps

def profile(
    measurements = None,
    formatter = None,
    exporters = None
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
            return profiler.results()
        return profiler_wrapper
    return function_profiler

class Profiler:
    """
    TODO:
    """

    def __init__(
        self,
        measurements = None,
        formatter = None,
        exporters = None
    ) -> None:
        self.measurements = measurements
        self.formatter = formatter
        self.exporters = exporters


    def start(self) -> None:
        """
        Starts a new profile run.
        """
        pass

    def stop(self) -> None:
        """
        Stops the current profile run.
        """
        pass

    def __call__(self, func: Type[Callable], *args, **kwargs) -> Any:
        """
        Profiles the given method.
        """
        self.start()

        func_ret = func(*args, **kwargs)

        self.stop()

        return func_ret




