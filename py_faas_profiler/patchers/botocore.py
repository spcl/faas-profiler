#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patcher for AWS botocore.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Callable, Type

import py_faas_profiler.patchers.base as base

from botocore.client import BaseClient


@dataclass
class AWSApiCall:
    service: str = None
    operation: str = None
    endpoint_url: str = None
    region_name: str = None
    api_params: dict = None
    http_uri: str = None
    http_method: str = None


@dataclass
class AWSApiResponse:
    http_code: int = None
    retry_attempts: int = None
    content_type: str = None
    content_length: int = None


class Patcher(base.BasePatcher):

    _logger = logging.getLogger("Botocore Patcher")
    _logger.setLevel(logging.INFO)

    target_module: str = "botocore"
    patch_only_on_import: bool = True

    def patch(self):
        self.add_patch_function(
            "botocore.client",
            "BaseClient._make_api_call",
            before_invocation=self.extract_call_information,
            after_invocation=self.extract_return_information)

    def extract_call_information(
        self,
        original_func: Type[Callable],
        instance: Type[BaseClient],
        args: tuple,
        kwargs: dict
    ) -> Type[AWSApiCall]:
        service = self._get_service(instance)

        meta = getattr(instance, "meta", None)

        operation = get_argument_value(
            args, kwargs, 0, "operation_name") if args else None
        api_params = get_argument_value(
            args, kwargs, 1, "api_params") if args else None

        http_method, http_uri = self._get_http_info(meta, operation)

        return AWSApiCall(
            service=service,
            operation=operation,
            endpoint_url=getattr(meta, "endpoint_url"),
            region_name=getattr(meta, "region_name"),
            api_params=api_params,
            http_uri=http_uri,
            http_method=http_method)

    def extract_return_information(self, function_return):
        return AWSApiResponse(
            http_code=function_return.get(
                "ResponseMetadata",
                {}).get("HTTPStatusCode"),
            retry_attempts=function_return.get(
                "ResponseMetadata",
                {}).get("RetryAttempts"),
            content_type=function_return.get("ContentType"),
            content_length=function_return.get("ContentLength"))

    def _get_http_info(
        self,
        meta,
        operation_name: str = None
    ) -> tuple:
        if operation_name and meta:
            try:
                op_model = meta.service_model.operation_model(operation_name)

                return (
                    op_model.http.get("method"),
                    op_model.http.get("requestUri"))
            except Exception as err:
                self._logger.error(f"Could not get operation model: {err}")
                return None, None

        return None, None

    def _get_service(self, instance: Type[BaseClient]) -> str:
        if not hasattr(instance, "_endpoint"):
            return

        return getattr(instance._endpoint, "_endpoint_prefix", None)


def get_argument_value(args, kwargs, pos, kw):
    try:
        return kwargs[kw]
    except KeyError:
        try:
            return args[pos]
        except IndexError:
            return None
