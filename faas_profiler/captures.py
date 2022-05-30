#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from contextlib import contextmanager
from functools import partial
from typing import List
from mock import patch


class InvocationCapture:

    def __init__(self, functions: List[str]) -> None:
        self.functions = functions
        self.patchers = [patch(
            target=func,
            new=partial(self._capture_invocation, func)
        ) for func in self.functions]

        self.invocations = {func: [] for func in self.functions}

    @contextmanager
    def capture(self):
        for patcher in self.patchers:
            patcher.start()

        yield

        for patcher in self.patchers:
            patcher.stop()

    def _capture_invocation(self, function_name, *args, **kwargs):
        self.invocations[function_name].append({
            "args": str(args),
            "kwargs": kwargs
        })
