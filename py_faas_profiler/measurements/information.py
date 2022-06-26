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
import re

from typing import Type
from datetime import datetime

from py_faas_profiler.measurements.base import Measurement, register_with_name
from py_faas_profiler.config import ProfileContext


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


@register_with_name("Information::Payload")
class Payload(Measurement):

    def setUp(
        self,
        profiler_context: Type[ProfileContext],
        config: dict = {}
    ) -> None:
        self.profiler_context = profiler_context

    def results(self) -> dict:
        payload_event = self.profiler_context.payload_event
        payload_context = self.profiler_context.payload_context
        environment_variables = self.profiler_context.environment_variables
        return {
            "event": {
                "type": payload_event.event_type,
                "size": payload_event.size,
                "content": payload_event.event
            },
            "context": {
                "size": payload_context.size,
                "content": payload_context.context
            },
            "environment": {
                "size": sys.getsizeof(environment_variables),
                "content": environment_variables
            }
        }
