#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storage interface
"""
from __future__ import annotations

import json
import boto3

from abc import ABC, abstractproperty, abstractmethod
from typing import Type
from botocore.exceptions import ClientError
from marshmallow import ValidationError
from functools import cached_property
from uuid import UUID
from os.path import basename, splitext

from faas_profiler.models import Trace, TraceRecord, Profile
from faas_profiler.utilis import Loggable


class RecordStorageError(RuntimeError):
    pass


class RecordStorage(ABC, Loggable):
    """
    Base class for all storage abstraction.
    Used this class to interact with the record storage.
    """

    PROFILES_PREFIX = "profiles/"
    PROFILES_FORMAT = PROFILES_PREFIX + "{profile_id}.json"
    UNPROCESSED_RECORDS_PREFIX = "unprocessed_records/"
    PROCESSED_RECORDS_PREFIX = "records/"
    PROCESSED_TRACES_PREFIX = "traces/"
    TRACE_FORMAT = PROCESSED_TRACES_PREFIX + "{trace_id}.json"

    def __init__(self):
        super().__init__()

    @abstractproperty
    def profile_ids(self) -> list[UUID]:
        """
        Returns a list of all profile IDs
        """
        pass

    @abstractproperty
    def number_of_profiles(self) -> int:
        """
        Returns the number of recorded profiles.
        """
        pass

    @property
    def has_profiles(self) -> bool:
        """
        Returns True if traces exists
        """
        return self.number_of_profiles > 0

    @abstractproperty
    def number_of_unprocessed_records(self) -> int:
        """
        Returns the number of unprocessed records.
        """
        pass

    @property
    def has_unprocessed_records(self) -> bool:
        """
        Returns True if unprocessed records exists.
        """
        return self.number_of_unprocessed_records > 0

    @abstractmethod
    def unprocessed_records(self):
        """
        Generator for all unprocessed records.
        """
        pass

    @abstractmethod
    def get_profile(self, profile_id: str):
        """
        Get a single profile.
        """
        pass

    @abstractmethod
    def store_trace(self, trace: Type[Trace]):
        """
        Store a new trace
        """
        pass

    @abstractmethod
    def mark_record_as_resolved(self, record_id: str):
        """
        Marks a record as resolved
        """
        pass

    @abstractmethod
    def store_profile(self, profile: Type[Profile]) -> None:
        """
        Stores a new profile.
        """
        pass

    @abstractmethod
    def get_trace(self, trace_id: UUID) -> Type[Trace]:
        """
        Gets a single trace.
        """
        pass


class S3RecordStorage(RecordStorage):
    """
    Storage implementation for AWS S3.
    """

    def __init__(self, bucket_name: str) -> None:
        super().__init__()

        self.bucket_name = bucket_name
        self.client = boto3.client('s3')

    @cached_property
    def profile_ids(self) -> list[UUID]:
        """
        Returns a list of all profile IDs
        """
        all_profile_keys = self._list_objects_with_paginator(
            prefix=self.PROFILES_PREFIX)

        if all_profile_keys is None or len(all_profile_keys) == 0:
            return []

        profile_ids = []
        all_profile_keys = sorted(
            all_profile_keys, key=lambda x: x["LastModified"], reverse=False)

        for profile_key in all_profile_keys:
            try:
                base = basename(profile_key.get("Key", ""))
                profile_ids.append(
                    UUID(splitext(base)[0]))
            except Exception as err:
                self.logger.error(
                    f"Failed to load profile ID: {err}")

        return profile_ids

    @property
    def number_of_profiles(self) -> int:
        """
        Returns the number of recorded profiles.
        """
        return len(self.profile_ids)

    def get_profile(self, profile_id: UUID):
        """
        Get a single profile.
        """
        _key = self.PROFILES_FORMAT.format(profile_id=str(profile_id))
        try:
            obj = self.client.get_object(Bucket=self.bucket_name, Key=_key)
        except ClientError as err:
            raise RecordStorageError(
                f"Failed to get object {_key}: {err}")

        if "Body" in obj:
            body = json.loads(obj["Body"].read().decode('utf-8'))
            try:
                return Profile.load(body)
            except ValidationError as err:
                raise RecordStorageError(
                    f"Failed to deserialize {body}: {err}")

    @cached_property
    def unprocessed_record_keys(self) -> list[str]:
        """
        Returns a list of unprocessed records sorted by last modified
        """
        record_keys = self._list_objects_with_paginator(
            prefix=self.UNPROCESSED_RECORDS_PREFIX)

        return [
            obj["Key"] for obj in sorted(
                record_keys,
                key=lambda x: x["LastModified"],
                reverse=False)]

    @property
    def number_of_unprocessed_records(self) -> int:
        """
        Returns the number of unprocessed records.
        """
        return len(self.unprocessed_record_keys)

    def unprocessed_records(self):
        """
        Generator for all unprocessed records.
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
                    continue

    def mark_record_as_resolved(self, record_id: str):
        """
        Marks a record as resolved
        """
        _record_key = f"{self.UNPROCESSED_RECORDS_PREFIX}{str(record_id)}.json"
        if _record_key in self.unprocessed_record_keys:
            _new_record_key = f"{self.PROCESSED_RECORDS_PREFIX}{str(record_id)}.json"
            self.client.copy_object(
                Bucket=self.bucket_name,
                CopySource=f"{self.bucket_name}/{_record_key}",
                Key=_new_record_key)
            self.client.delete_object(Bucket=self.bucket_name, Key=_record_key)
        else:
            self.logger.info(
                f"Record with ID {record_id} is already processed.")

    def store_profile(self, profile: Type[Profile]) -> None:
        """
        Stores a new profile.
        """
        profile_data = profile.dump()
        profile_json = json.dumps(
            profile_data,
            ensure_ascii=False,
            indent=None
        ).encode('utf-8')

        _key_name = f"{self.PROFILES_PREFIX}{profile.profile_id}.json"
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=_key_name,
            Body=profile_json)

    def store_trace(self, trace: Type[Trace]):
        """
        Stores a new trace.
        """
        trace_data = trace.dump()
        trace_json = json.dumps(
            trace_data,
            ensure_ascii=False,
            indent=None
        ).encode('utf-8')

        _key_name = f"{self.PROCESSED_TRACES_PREFIX}{trace.trace_id}.json"
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=_key_name,
            Body=trace_json)

    def get_trace(self, trace_id: UUID) -> Type[Trace]:
        """
        Gets a single trace.
        """
        _key = self.TRACE_FORMAT.format(trace_id=str(trace_id))
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

    """
    Private methods
    """

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
