#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for monkey patching.
"""

from importlib import import_module
from typing import Type

from py_faas_profiler.patchers.base import BasePatcher

_PATCHED_MODULES = dict()


def patch_module(module: str) -> Type[BasePatcher]:
    path = f"py_faas_profiler.patchers.{module}"

    if path in _PATCHED_MODULES:
        print("in path")
        return _PATCHED_MODULES[path]

    else:
        try:
            patcher_module = import_module(path)
        except ImportError:
            print(f"{path} not found")
            return

        if hasattr(patcher_module, "Patcher"):
            patcher = patcher_module.Patcher()
            # TODO: Handle patch_only_on_import

            return patcher
        else:
            print(f"Patcher not found in {patcher_module}")
