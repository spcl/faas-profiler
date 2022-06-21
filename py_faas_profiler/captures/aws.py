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


@register_with_name("AWS::S3Capture")
class S3Capture(Capture):

    def __init__(self) -> None:
        self.patcher = patch_module("botocore")
        self._s3_captures = []

    def start(self):
        self.patcher.add_capture_observer(self)

    def __call__(
        self,
        patch_event: Type[PatchEvent],
        aws_api_call: Type[AWSApiCall],
        aws_api_response: Type[AWSApiResponse]
    ) -> None:
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

    def results(self) -> dict:
        return {
            "invocations": self._s3_captures
        }
