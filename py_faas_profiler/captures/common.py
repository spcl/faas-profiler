#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for AWS invocation capturing.
"""

from typing import Type

from py_faas_profiler.patchers import patch_module
from py_faas_profiler.patchers.base import PatchEvent
from py_faas_profiler.patchers.botocore import AWSApiCall, AWSApiResponse

from py_faas_profiler.captures.base import Capture, register_with_name


# @register_with_name("Common::IOCapture")
# class IOCapture(Capture):

#     def __init__(self) -> None:
#         self.patcher = patch_module("io")
#         self._s3_captures = []

#     def start(self):
#         self.patcher.add_capture_observer(self)

#     def __call__(
#         self,
#         patch_event: Type[PatchEvent],
#         aws_api_call: Type[AWSApiCall],
#         aws_api_response: Type[AWSApiResponse]
#     ) -> None:
#         pass

#     def stop(self) -> None:
#         self.patcher.remove_capture_observer(self)

#     def results(self) -> dict:
#         return {}



