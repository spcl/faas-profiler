#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for base patchers.
"""

from __future__ import annotations

import logging
import importlib

from dataclasses import dataclass
from collections import namedtuple
from time import time
from typing import Any, Callable, List, Type
from functools import partial
from threading import Lock
from wrapt import wrap_function_wrapper


class RequiredModuleMissingError(RuntimeError):
    pass


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

    PatchedFunction = namedtuple(
        'PatchedFunction',
        'module_name class_name function_name before_invocation after_invocation')

    @property
    def patched_functions(self) -> list[Type[PatchedFunction]]:
        return []

    def __init__(self,) -> None:
        self._lock = Lock()
        self._patch_active: bool = False

        self._patched_functions: List[BasePatcher.PatchedFunction] = []
        self._capture_oberservers = set()

        # self.target_module = self._import_target_module()

    def add_capture_observer(self, observer):
        if not callable(observer):
            raise ValueError(
                f"{observer} must be callable to act as oberserver.")

        self._capture_oberservers.add(observer)

    def remove_capture_observer(self, oberserver):
        if oberserver in self._capture_oberservers:
            self._capture_oberservers.remove(oberserver)

    def add_patch_function(
        self,
        module_name: str,
        function_name: str,
        before_invocation: Callable = None,
        after_invocation: Callable = None
    ) -> None:
        a, *b = function_name.split(".")
        _function_name = b[0] if b else a
        _class_name = a if b else None

        # breakpoint()

        self._patched_functions.append(BasePatcher.PatchedFunction(
            module_name=module_name,
            class_name=_class_name,
            function_name=_function_name,
            before_invocation=before_invocation,
            after_invocation=after_invocation))

        wrap_function_wrapper(
            module=module_name,
            name=function_name,
            wrapper=partial(self._function_wrapper,
                            before_invocation=before_invocation,
                            after_invocation=after_invocation))

    def patch(self):
        pass

    def unpatch(self):
        pass

    def start(self):
        if self._patch_active:
            return

        self.patch()
        self._patch_active = True

    def stop(self):
        if not self._patch_active:
            return

        self.unpatch()
        self._unpatch_functions()
        self._patch_active = False

    def _unpatch_functions(self):
        for patched_function in self._patched_functions:
            module = importlib.import_module(patched_function.module_name)
            if patched_function.class_name:
                klass = getattr(module, patched_function.class_name)
                func_wrapper = getattr(klass, patched_function.function_name)

                setattr(
                    klass,
                    patched_function.function_name,
                    func_wrapper.__wrapped__)
            else:
                # breakpoint()
                func_wrapper = getattr(module, patched_function.function_name)
                setattr(
                    module,
                    patched_function.function_name,
                    func_wrapper.__wrapped__)

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
