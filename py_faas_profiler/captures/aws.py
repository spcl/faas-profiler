#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for AWS invocation capturing.
"""

from typing import Type

from py_faas_profiler.patchers import patch_module
from py_faas_profiler.patchers.base import PatchEvent
from py_faas_profiler.patchers.botocore import AWSApiCall, AWSApiResponse
from py_faas_profiler.patchers.io import IOCall, IOReturn

from py_faas_profiler.captures.base import Capture, register_with_name


@register_with_name("AWS::S3Capture")
class S3Capture(Capture):

    def __init__(self, config: dict = {}) -> None:
        self.patcher = patch_module("botocore")
        self._s3_captures = []

    def start(self):
        self.patcher.start()
        self.patcher.add_capture_observer(self)

    def __call__(
        self,
        patch_event: Type[PatchEvent],
        aws_api_call: Type[AWSApiCall],
        aws_api_response: Type[AWSApiResponse]
    ) -> None:
        if aws_api_response is None or aws_api_response is None:
            return

        if aws_api_call.service != "s3":
            return

        self._s3_captures.append({
            "operation": aws_api_call.operation,
            "bucket": aws_api_call.api_params.get("Bucket"),
            "key": aws_api_call.api_params.get("Key"),
            "api_params": aws_api_call.api_params,
            "request_url": aws_api_call.endpoint_url,
            "request_uri": aws_api_call.http_uri,
            "request_method": aws_api_call.http_method,
            "request_status": aws_api_response.http_code,
            "size": aws_api_response.content_length,
            "execution_time": patch_event.execution_time
        })

    def stop(self) -> None:
        self.patcher.remove_capture_observer(self)
        self.patcher.stop()

    def invocations(self) -> list:
        return self._s3_captures


@register_with_name("AWS::EFSCapture")
class EFSCapture(Capture):

    def __init__(self, config: dict = {}) -> None:
        self.mounting_points = config.get("mount_points")

        if not self.mounting_points:
            raise ValueError(
                "Cannot initialise EFSCapture without mounting points")

        self.patcher = patch_module("io")
        self._efs_captures = []

    def start(self):
        self.patcher.start()
        self.patcher.add_capture_observer(self)

    def __call__(
        self,
        patch_event: Type[PatchEvent],
        io_call: Type[IOCall],
        io_return: Type[IOReturn]
    ) -> None:
        for monting_point in self.mounting_points:
            if io_call.file.startswith(monting_point):
                self._efs_captures.append({
                    "efs_mount": monting_point,
                    "file": io_call.file,
                    "mode": self._determine_mode(io_call.mode),
                    "encoding": io_return.encoding,
                    "io_type": str(io_return.wrapper_type),
                    "execution_time": patch_event.execution_time
                })

    def stop(self) -> None:
        self.patcher.remove_capture_observer(self)
        self.patcher.stop()

    def invocations(self) -> list:
        return self._efs_captures

    def _determine_mode(self, mode: str) -> str:
        if "r+" in mode or "w+" in mode or "a" in mode:
            return "read/write"

        if "r" in mode:
            return "read"

        if "w" in mode or "a" in mode:
            return "write"
