#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import glob
import fnmatch
import re

import boto3
import botocore.exceptions

from typing import List

from .config import config


def result_key_by_id(profile_run_id: str) -> str:
    return f"fp_results_{profile_run_id}.json"


def store_parsed_result(result: dict) -> bool:
    profile_run_id = result.get("profile_run_id")
    if profile_run_id is None:
        raise ValueError("Need profile run id to store results")

    filename = result_key_by_id(result["profile_run_id"])

    if config.is_development:
        return _store_locally(result, filename)
    else:
        return _upload_to_s3(result, filename)


def _store_locally(result: dict, filename: str) -> str:
    config.ensure_local_path()

    file = os.path.join(config.local_results_path, filename)
    if os.path.exists(file):
        raise RuntimeError(
            f"Results for {result['profile_run_id']} already exists.")

    with open(file, "w") as fp:
        json.dump(result, fp)

    return file


def _upload_to_s3(result: dict, filename: str) -> str:
    s3_client = boto3.client('s3')

    json_body = json.dumps(
        result,
        ensure_ascii=False,
        indent=None
    ).encode('utf-8')

    try:
        s3_client.head_object(
            Bucket=config.result_s3_bucket,
            Key=filename)

        raise RuntimeError(
            f"Results for {result['profile_run_id']} already exists.")
    except botocore.exceptions.ClientError:
        key = s3_client.put_object(
            Bucket=config.result_s3_bucket,
            Key=filename,
            Body=json_body)

        return key


def get_all_results() -> List[dict]:
    if config.is_development:
        return _get_local_results()
    else:
        return _get_s3_results()


def get_result_by_id(profile_run_id: str) -> dict:
    if config.is_development:
        results = _get_local_results(profile_run_id)
    else:
        results = _get_s3_results(profile_run_id)

    if len(results) > 1:
        raise RuntimeError(
            "Ambiguous search. Could not find a unique profile run for the given ID.")

    return results[0] if results else None


def _get_local_results(filter_by_id: str = "*") -> List[dict]:
    results = []

    paths = glob.glob(
        os.path.join(
            config.local_results_path,
            result_key_by_id(filter_by_id)))
    for path in paths:
        with open(path, 'r') as fp:
            results.append(json.load(fp))

    return results


def _get_s3_results(filter_by_id: str = "*") -> List[dict]:
    results = []

    s3_client = boto3.client('s3')
    objects = s3_client.list_objects_v2(
        Bucket=config.result_s3_bucket)['Contents']
    for object in objects:
        key_regex = fnmatch.translate(result_key_by_id(filter_by_id))
        if re.match(key_regex, object["Key"]):
            file = s3_client.get_object(
                Bucket=config.result_s3_bucket, Key=object["Key"])
            results.append(json.load(file["Body"]))

    return results
