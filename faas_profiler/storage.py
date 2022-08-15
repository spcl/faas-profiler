#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storage interface
"""

import json
import boto3

from typing import Type
from botocore.exceptions import ClientError
from marshmallow import ValidationError

from faas_profiler_core.models import TraceRecord

from faas_profiler.models import Trace
from faas_profiler.utilis import Loggable


class RecordStorageError(RuntimeError):
    pass


class RecordStorage(Loggable):
    pass


class S3RecordStorage(RecordStorage):

    TRACE_FOLDER = "traces/"
    UNPROCESSED_FOLER = "unprocessed_records/"

    def __init__(self, bucket_name: str) -> None:
        super().__init__()

        self.bucket_name = bucket_name
        self.client = boto3.client('s3')

        self.unprocessed_record_keys = self._list_unprocessed_record_keys()
        self.trace_keys = self._list_trace_keys()

    def unprocessed_records(self):
        """
        Generator for all unprocessed records
        """
        for key in self.unprocessed_record_keys:
            try:
                obj = self.client.get_object(Bucket=self.bucket_name, Key=key)
            except ClientError as err:
                self.logger.error(
                    f"Failed to get object {key}: {err}")
                continue

            if "Body" in obj:
                body = json.loads(obj["Body"].read().decode('utf-8'))
                try:
                    yield TraceRecord.load(body)
                except ValidationError as err:
                    self.logger.error(
                        f"Failed to deserialize {body}: {err}")

    @property
    def number_of_traces(self) -> int:
        """
        Returns the number of traces
        """
        return len(self.trace_keys)

    @property
    def has_traces(self) -> bool:
        """
        Returns True if traces exists
        """
        return self.number_of_traces > 0

    def traces(self):
        """
        Generator for all traces
        """
        for key in self.trace_keys:
            try:
                obj = self.client.get_object(Bucket=self.bucket_name, Key=key)
            except ClientError as err:
                self.logger.error(
                    f"Failed to get object {key}: {err}")
                continue

            if "Body" in obj:
                body = json.loads(obj["Body"].read().decode('utf-8'))
                try:
                    yield Trace.load(body)
                except ValidationError as err:
                    self.logger.error(
                        f"Failed to deserialize {body}: {err}")

    def get_trace(self, trace_id: str) -> Type[Trace]:
        """
        Returns one trace by ID
        """
        _key = f"{self.TRACE_FOLDER}{str(trace_id)}.json"
        try:
            obj = self.client.get_object(Bucket=self.bucket_name, Key=_key)
        except ClientError as err:
            raise RecordStorageError(
                f"Failed to get object {_key}: {err}")

        if "Body" in obj:
            body = json.loads(obj["Body"].read().decode('utf-8'))
            try:
                return Trace.load(body)
            except ValidationError as err:
                raise RecordStorageError(
                    f"Failed to deserialize {body}: {err}")

    def upload_trace(self, trace: Type[Trace]):
        """
        Uploads trace to S3
        """
        trace_data = trace.dump()
        trace_json = json.dumps(
            trace_data,
            ensure_ascii=False,
            indent=None
        ).encode('utf-8')

        _key_name = f"{self.TRACE_FOLDER}{trace.trace_id}.json"
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=_key_name,
            Body=trace_json)

    """
    Private methods
    """

    def _list_unprocessed_record_keys(self) -> list:
        """
        Returns a list of unprocessed records sorted by last modified
        """
        record_keys = self._list_objects_with_paginator(
            prefix=self.UNPROCESSED_FOLER)

        return [
            obj["Key"] for obj in sorted(
                record_keys,
                key=lambda x: x["LastModified"],
                reverse=False)]

    def _list_trace_keys(self) -> list:
        """
        Returns a list of traces
        """
        trace_keys = self._list_objects_with_paginator(
            prefix=self.TRACE_FOLDER)

        return [
            obj["Key"] for obj in sorted(
                trace_keys,
                key=lambda x: x["LastModified"],
                reverse=False)]

    def _list_objects_with_paginator(self, prefix: str = None) -> list:
        """
        Returns a list of object with pagination
        """
        keys = []
        paginator = self.client.get_paginator('list_objects')
        page_iterator = paginator.paginate(
            Bucket=self.bucket_name,
            Prefix=prefix)

        for page in page_iterator:
            if "Contents" in page:
                keys += page["Contents"]

        return keys
