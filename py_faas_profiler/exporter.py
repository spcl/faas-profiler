#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for exporting and collecting results.
"""

import json
import yaml
import logging
import boto3

from os import path
from functools import cached_property
from typing import Any, List, Type

from py_faas_profiler.captures.base import Capture
from py_faas_profiler.config import Config, ProfileContext, get_faas_profiler_version
from py_faas_profiler.utilis import Registerable, registerable_key


def json_formatter(raw_data: list) -> str:
    return json.dumps(
        raw_data,
        ensure_ascii=False,
        indent=None
    ).encode('utf-8')


def yaml_formatter(raw_data: list) -> str:
    return yaml.dump(
        raw_data,
        sort_keys=False,
        default_flow_style=False
    ).encode('utf-8')


class ResultsCollector:

    _logger = logging.getLogger("ResultsCollector")
    _logger.setLevel(logging.INFO)

    def __init__(
        self,
        config: Type[Config],
        profile_context: Type[ProfileContext],
        captures: List[Type[Capture]]
    ) -> None:
        self.config = config
        self.profile_context = profile_context
        self.captures = captures

    @cached_property
    def raw_data(self) -> list:
        return {
            "profile_run_id": str(self.profile_context.profile_run_id),
            "py_faas_version": get_faas_profiler_version(),
            "measurements": self._collect_results(self.config.measurements),
            "captures": self._collect_capture_results()
        }

    def format(self, formatter=json_formatter) -> Any:
        return formatter(self.raw_data)

    def _collect_capture_results(self):
        return [{
            "name": c.name,
            "invocations": c.invocations()
        } for c in self.captures]

    def _collect_results(
            self, config_item_list: List[Type[Config.ConfigItem]]) -> list:
        if not config_item_list:
            return []

        results_list = []
        for config_item in config_item_list:
            results_file = path.join(
                self.profile_context.tmp_results_dir,
                f"{registerable_key(config_item.name)}.json")

            if path.exists(results_file):
                results_list.append({
                    "name": config_item.name,
                    "results": self._parse_result_file(results_file)
                })
            else:
                self._logger.warn(
                    f"No result file found for: {config_item.name}. Skipping")

        return results_list

    def _parse_result_file(self, file: str) -> dict:
        try:
            with open(file, "r") as fp:
                try:
                    return json.load(fp)
                except json.JSONDecodeError as err:
                    self._logger.error(
                        f"Parsing result file {file} failed: {err}")
        except IOError as err:
            self._logger.error(f"Opening result file {file} failed: {err}")

        return {}


class Exporter(Registerable):
    def __init__(
            self,
            profile_context: Type[ProfileContext],
            config: dict = {}) -> None:
        self.profile_context = profile_context
        self.config = config

    def dump(self, results_collector: Type[ResultsCollector]) -> None:
        pass


@Exporter.register("S3Uploader")
class S3Uploader(Exporter):

    def __init__(
            self,
            profile_context: Type[ProfileContext],
            config: dict = {}) -> None:
        self.bucket = config.get("bucket")
        self.folder = config.get("folder")
        self.format = config.get("format", "json")
        self.file_prefix = "fp_results_"

        if not self.bucket:
            raise ValueError("Cannot initialise S3Uploader without bucket")

        self.s3_client = boto3.client('s3')
        super().__init__(profile_context, config)

    def dump(self, results_collector: Type[ResultsCollector]) -> None:
        if self.format == "json":
            key_name = self._get_key_name("json")
            body = results_collector.format(formatter=json_formatter)
        elif self.format == "yaml":
            key_name = self._get_key_name("yaml")
            body = results_collector.format(formatter=yaml_formatter)
        else:
            raise NotImplementedError(
                f"No formatter implemented for {self.format}")

        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key_name,
            Body=body)

        return key_name

    def _get_key_name(self, file_ext: str) -> str:
        uuid = self.profile_context.profile_run_id
        key_name = f"{self.file_prefix}{uuid}.{file_ext}"
        if self.folder:
            key_name = f"{self.folder}/{key_name}"

        return key_name
