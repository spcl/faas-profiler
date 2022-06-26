#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patcher for IO botocore.
"""

from __future__ import annotations

import io
import logging

from dataclasses import dataclass
from typing import Callable, Type

import py_faas_profiler.patchers.base as base
from py_faas_profiler.utilis import get_arg_by_key_or_pos


@dataclass
class IOCall:
    file: str = None
    mode: str = None
    encoding: str = None


@dataclass
class IOReturn:
    wrapper_type: io.IOBase = None
    file: str = None
    mode: str = None
    encoding: str = None


class Patcher(base.BasePatcher):

    _logger = logging.getLogger("IO Patcher")
    _logger.setLevel(logging.INFO)

    # target_module: str = "builtins"
    patch_only_on_import: bool = True

    def patch(self):
        self.add_patch_function(
            "builtins",
            "open",
            before_invocation=self.extract_call_information,
            after_invocation=self.extract_return_information)

    def extract_call_information(
        self,
        original_func: Type[Callable],
        instance,
        args,
        kwargs
    ) -> Type[IOCall]:
        file = get_arg_by_key_or_pos(args, kwargs, 0, "file")
        mode = get_arg_by_key_or_pos(args, kwargs, 1, "mode")
        encoding = get_arg_by_key_or_pos(args, kwargs, 3, "encoding")

        return IOCall(str(file), str(mode), str(encoding))

    def extract_return_information(self, function_return):
        if not hasattr(function_return, "__class__"):
            return

        io_class = function_return.__class__
        if not issubclass(io_class, io.IOBase):
            return

        return IOReturn(
            wrapper_type=io_class,
            file=str(getattr(function_return, "name", None)),
            mode=str(getattr(function_return, "mode", None)),
            encoding=str(getattr(function_return, "encoding", None)))
