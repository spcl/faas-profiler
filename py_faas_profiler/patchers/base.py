#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for base patchers.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
import importlib
from time import time
from typing import Any, Callable, Dict, List, Type
from functools import partial
from threading import Lock
from wrapt import ObjectProxy, wrap_function_wrapper


class RequiredModuleMissingError(RuntimeError):
    pass


@dataclass
class PatchedFunction:
    module_name: str
    function_name: str
    before_invocation: Callable = None
    after_invocation: Callable = None


@dataclass
class TracedInstance:
    module_name: str
    class_name: str


@dataclass
class PatchEvent:
    function_name: str
    instance_name: str
    execution_time: int


class BasePatcher:

    _logger = logging.getLogger("Base Patcher")
    _logger.setLevel(logging.INFO)

    target_module: str = None
    patch_only_on_import: bool = False

    @property
    def patched_functions(self) -> list[Type[PatchedFunction]]:
        return []

    def __init__(self,) -> None:
        self._lock = Lock()
        self._patch_active: bool = False

        self._capture_oberservers = set()

        self.target_module = self._import_target_module()

        self.patch()

    def add_capture_observer(self, observer):
        if not callable(observer):
            raise ValueError(
                f"{observer} must be callable to act as oberserver.")

        self._capture_oberservers.add(observer)

    def remove_capture_observer(self, oberserver):
        if oberserver in self._capture_oberservers:
            self._capture_oberservers.remove(oberserver)

    def patch(self):
        if getattr(self.target_module, "_fp_patched", False):
            return

        setattr(self.target_module, "_fp_patched", True)

        for function_patch in self.patched_functions:
            wrap_function_wrapper(
                module=function_patch.module_name,
                name=function_patch.function_name,
                wrapper=partial(
                    self._function_wrapper,
                    before_invocation=function_patch.before_invocation,
                    after_invocation=function_patch.after_invocation))

    def unpatch(self):
        pass

    def _function_wrapper(
        self,
        original_func: Type[Callable],
        instance: Type[Any],
        args: tuple,
        kwargs: dict,
        before_invocation: Type[Callable] = None,
        after_invocation: Type[Callable] = None
    ) -> Any:
        event = PatchEvent(original_func.__name__, str(instance), 0)

        before_result = None
        if before_invocation:
            try:
                before_result = before_invocation(
                    original_func, instance, args, kwargs)
            except Exception as err:
                self._logger.error(f"Before invocation patcher failed: {err}")

        invocation_start = time()
        func_return = original_func(*args, **kwargs)
        event.execution_time = time() - invocation_start

        after_result = None
        if after_invocation:
            after_result = after_invocation(func_return)

        self._notify(event, before_result, after_result)

        return func_return

    def _notify(self, patch_event, before_result=None, after_result=None):
        for capture_oberserver in self._capture_oberservers:
            capture_oberserver(patch_event, before_result, after_result)

    def _import_target_module(self):
        with self._lock:
            try:
                return importlib.import_module(self.target_module)
            except ImportError:
                raise RequiredModuleMissingError(
                    f"Required modules are missing: {self.target_module}")
