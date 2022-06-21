#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for invocation capturing.
"""

from __future__ import annotations

from typing import Any

from py_faas_profiler.utilis import Registerable


class Capture(Registerable):

    def __init__(self, config: dict = {}) -> None:
        pass

    def start(self) -> None:
        pass

    def __call__(
        self,
        patch_event: Any,
        before_result: Any = None,
        after_result: Any = None
    ) -> None:
        pass

    def stop(self) -> None:
        pass

    def invocations(self) -> list:
        return []


register_with_name = Capture.register
