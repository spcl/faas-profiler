#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for information extraction:
- Environment
- OperatingSystem
"""

import sys
import platform
import os
import pkg_resources
import logging
import psutil

from datetime import datetime

from py_faas_profiler.measurements.base import Measurement, register_with_name


@register_with_name("Information::Environment")
class Environment(Measurement):

    _logger = logging.getLogger("Information::Environment")
    _logger.setLevel(logging.INFO)

    def results(self) -> dict:
        return {
            "runtime": {
                "name": "python",
                "version": sys.version,
                "implementation": platform.python_implementation(),
                "compiler": platform.python_compiler()
            },
            "byteOrder": sys.byteorder,
            "platform": sys.platform,
            "interpreterPath": sys.executable,
            "Packages": self._installed_packages(),
        }

    def _installed_packages(self) -> list:
        try:
            installed_packages = pkg_resources.working_set
            return sorted(["%s==%s" % (i.key, i.version)
                          for i in installed_packages])
        except Exception as exc:
            self._logger.warn(f"Could not get installed packages: {exc}")
            return []


@register_with_name("Information::OperatingSystem")
class OperatingSystem(Measurement):

    def results(self) -> dict:
        uname = os.uname()
        return {
            "bootTime": self._get_boot_time(),
            "system": uname.sysname,
            "nodeName": uname.nodename,
            "release": uname.release,
            "machine": uname.machine,
        }

    def _get_boot_time(self) -> str:
        bt = datetime.fromtimestamp(psutil.boot_time())
        return f"{bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}"
