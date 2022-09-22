#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler global configuration
"""

from faas_profiler_core.storage import RecordStorage, S3RecordStorage, GCPRecordStorage
from faas_profiler_core.constants import Provider
from typing import Type
import os
from os.path import abspath, dirname, join

PACKAGE_ROOT = abspath(dirname(__file__))
PROJECT_ROOT = abspath(dirname(PACKAGE_ROOT))


class Config:
    """
    FaaS-Profiler Visualizer configuration
    """

    def __init__(self) -> None:
        self._storage_bucket = None
        self._provider = None
        self._storage: Type[RecordStorage] = None
        self._region = None
        self._project_id = None

        os.makedirs(self.temporary_dir, exist_ok=True)

    @property
    def provider(self) -> Provider:
        """
        Returns the cloud provider where the Visualizer is deployed.
        """
        return self._provider

    @provider.setter
    def provider(self, provider: str) -> None:
        if provider == "aws":
            self._provider = Provider.AWS
        elif provider == "gcp":
            self._provider = Provider.GCP
        else:
            raise RuntimeError(f"Invalid provider {provider}")

    @property
    def storage_bucket(self) -> str:
        """
        Returns the bucket name for the records storage
        """
        return self._storage_bucket

    @property
    def region(self) -> str:
        return self._region

    @region.setter
    def region(self, region) -> None:
        self._region = region

    @storage_bucket.setter
    def storage_bucket(self, bucket) -> None:
        self._storage_bucket = bucket

    @property
    def project_id(self) -> str:
        """
        GCP project id
        """
        return self._project_id

    @project_id.setter
    def project_id(self, project_id) -> None:
        self._project_id = project_id

    @property
    def storage(self) -> Type[RecordStorage]:
        """
        Returns a storage.
        """
        if self._storage is not None:
            return self._storage

        if not self.provider or not self.storage_bucket:
            raise RuntimeError(
                "Please set first provider and record bucket name")

        if self.provider == Provider.AWS:
            self._storage = S3RecordStorage(self.storage_bucket, self.region)
        elif self.provider == Provider.GCP:
            self._storage = GCPRecordStorage(
                self.project_id, self.region, self.storage_bucket)

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

    @property
    def temporary_dir(self) -> str:
        """
        Returns the directory for temporary files.
        """
        return join(PROJECT_ROOT, "profiler_tmp")


config = Config()
