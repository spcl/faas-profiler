#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defines different methods to export the results.
"""

from abc import ABC, abstractmethod
from io import BytesIO
from os import path

import boto3
from botocore.exceptions import ClientError


class Exporter(ABC):

    @abstractmethod
    def export(self, file_path: str) -> bool:
        pass


class S3Exporter(Exporter):

    def __init__(self, bucket, folder="results") -> None:
        self.s3_client = boto3.client('s3')
        self.bucket = bucket
        self.folder = folder

    def export(self, file_path) -> bool:
        file = open(file_path, "rb").read()
        file_as_binary = BytesIO(file)
        try:
            self.s3_client.upload_fileobj(
                file_as_binary,
                self.bucket,
                f"{self.folder}/{path.basename(file_path)}")
        except ClientError as e:
            print(e)
            return False

        return True
