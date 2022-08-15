#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler global configuration
"""

from os.path import abspath, dirname, join

PACKAGE_ROOT = abspath(dirname(__file__))
PROJECT_ROOT = abspath(dirname(PACKAGE_ROOT))

import os
from typing import Type

from faas_profiler_core.constants import Provider

from faas_profiler.storage import RecordStorage, S3RecordStorage

class Config:
    """
    FaaS-Profiler Visualizer configuration
    """

    def __init__(self) -> None:
        self._storage = S3RecordStorage(self.storage_bucket)

    @property
    def provider(self) -> Provider:
        """
        Returns the cloud provider where the Visualizer is deployed.
        """
        # TODO: make this dynamic
        return Provider.AWS

    @property
    def region(self):
        """
        Returns the region where the Visualizer is deployed.
        """
        if self.provider == Provider.AWS:
            return os.environ.get("AWS_REGION", "eu-central-1")

    @property
    def storage_bucket(self) -> str:
        """
        Returns the bucket name for the records storage
        """
        return os.environ.get("AWS_RECORDS_BUCKET", "faas-profiler-records")

    @property
    def storage(self) -> Type[RecordStorage]:
        """
        Returns a storage.
        """
        return self._storage


    @property
    def examples_dir(self) -> str:
        """
        Returns the directory to serverless examples.
        """
        return join(PROJECT_ROOT, "examples")

    @property
    def templates_dir(self) -> str:
        """
        Returns the directory to templates.
        """
        return join(PACKAGE_ROOT, "templates")


config = Config()
