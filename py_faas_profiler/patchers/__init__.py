#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for monkey patching.
"""

import logging

from importlib import import_module
from typing import Type

from py_faas_profiler.patchers.base import BasePatcher

PATCHED_MODULES = dict()
_PATCHERS_MODULE = "py_faas_profiler.patchers.{}"

_logger = logging.getLogger("Patchers")
_logger.setLevel(logging.INFO)


def patch_module(module: str) -> Type[BasePatcher]:
    path = _PATCHERS_MODULE.format(module)

    if path in PATCHED_MODULES:
        _logger.info(
            f"Patcher for {module} already created. Return cached one.")
        return PATCHED_MODULES[path]

    else:
        try:
            patcher_module = import_module(path)
        except ImportError:
            _logger.error(f"Could not import patcher module: {path}")
        else:
            if hasattr(patcher_module, "Patcher"):
                patcher = patcher_module.Patcher()
                # TODO: Handle patch_only_on_import

                PATCHED_MODULES[module] = patcher
                return patcher
            else:
                _logger.error(f"Patcher class not found in {patcher_module}")


def unpatch_modules():
    global PATCHED_MODULES

    for patcher in PATCHED_MODULES.values():
        patcher.stop()

    PATCHED_MODULES = {}
