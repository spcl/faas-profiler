import faas_profiler_python as fp

import json
import os
import logging
import boto3
import random

from uuid import uuid4

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

DATA_BUCKET_NAME = os.environ.get(
    "MATRIX_BUCKET_NAME",
    "matrix-multiplication-data")
DATA_BUCKET_REGION = os.environ.get("MATRIX_BUCKET_REGION", "eu-central-1")

MATRIX_PATTERN = "{run_id}/{matrix}.json"
SUBMATRIX_PATTERN = "{run_id}/worker_{worker_id}.json"
SUBMATRIX_RESULT_PATTERN = "{run_id}/worker_{worker_id}_results.json"

s3_client = boto3.client('s3', region_name=DATA_BUCKET_REGION)

"""
Helper
"""


def get_s3_json(bucket, key):
    get_response = s3_client.get_object(Bucket=bucket, Key=key)
    return json.loads(get_response['Body'].read())


def store_s3_json(obj, bucket, key):
    s3_client.put_object(
        Body=json.dumps(obj).encode('utf-8'), Bucket=bucket, Key=key)


"""
Handler
"""

@fp.profile()
def make_matrix(event, context):
    """
    Create random matrix
    """
    size = event.get("size", 500)
    max_value = event.get("maxValue", 1e5)
    min_value = event.get("minValue", -1e5)

    def _generate_matrix() -> list:
        matrix = []
        for _ in range(0, size):
            row = []
            for _ in range(0, size):
                row.append(random.uniform(min_value, max_value))

            matrix.append(row)

        return matrix

    A = _generate_matrix()
    B = _generate_matrix()

    run_id = uuid4()
    matrix_a_key = MATRIX_PATTERN.format(run_id=run_id, matrix="A")
    matrix_b_key = MATRIX_PATTERN.format(run_id=run_id, matrix="B")

    # Upload A
    logger.info(
        f"Uploading A to S3 (bucket={DATA_BUCKET_NAME}, key={matrix_a_key})")
    store_s3_json(A, DATA_BUCKET_NAME, matrix_a_key)

    # Upload A
    logger.info(
        f"Uploading B to S3 (bucket={DATA_BUCKET_NAME}, key={matrix_b_key})")
    store_s3_json(B, DATA_BUCKET_NAME, matrix_b_key)

    return {
        "runID": str(run_id),
        "size": size
    }

@fp.profile()
def schedule_work(event, context):
    """
    Schedule parallel work
    """
    run_id = event.get("runID")
    worker_count = int(event.get("workerCount", 5))
    size = int(event.get("size"))

    if not run_id:
        raise RuntimeError("Cannot schedule work without run ID")

    if not size:
        raise RuntimeError("Cannot schedule work without size")

    logger.info(f"Build tasks for {run_id} and worker count {worker_count}")
    tasks = [[] for _ in range(0, worker_count)]

    task_count = 0
    for x in range(0, size):
        for y in range(0, size):
            worker_id = task_count % worker_count
            tasks[worker_id].append([x, y])

            task_count += 1

    for worker_id, tasks in enumerate(tasks):
        submatrix_key = SUBMATRIX_PATTERN.format(
            run_id=run_id, worker_id=worker_id)
        store_s3_json(tasks, DATA_BUCKET_NAME, submatrix_key)

    return event

@fp.profile()
def multiply_parallel(event, context):
    """
    Multiplication worker
    """
    run_id = event.get("runID")
    worker_id = int(event.get("workerID"))
    size = int(event.get("size"))

    if not run_id:
        raise RuntimeError("Cannot perform work without run ID")

    if worker_id is None:
        raise RuntimeError("Cannot perform work without worker ID")

    if not size:
        raise RuntimeError("Cannot perform work without size")

    A = get_s3_json(
        DATA_BUCKET_NAME,
        MATRIX_PATTERN.format(
            run_id=run_id,
            matrix="A"))
    B = get_s3_json(
        DATA_BUCKET_NAME,
        MATRIX_PATTERN.format(
            run_id=run_id,
            matrix="B"))

    tasks = get_s3_json(
        DATA_BUCKET_NAME,
        SUBMATRIX_PATTERN.format(
            run_id=run_id,
            worker_id=worker_id))

    results = {}
    for task in tasks:
        result = 0
        for i in range(0, size):
            result += A[task[0]][i] * B[i][task[1]]

        results[f"{task[0]}#{task[1]}"] = result

    store_s3_json(results, DATA_BUCKET_NAME, SUBMATRIX_RESULT_PATTERN.format(
        run_id=run_id, worker_id=worker_id))

    return event

@fp.profile()
def combine_results(event, context):
    """
    Combines results
    """
    run_id = event.get("runID")
    worker_count = int(event.get("workerCount"))
    size = int(event.get("size"))

    if not run_id:
        raise RuntimeError("Cannot combine work without run ID")

    if worker_count is None:
        raise RuntimeError("Cannot combine work without worker count")

    if not size:
        raise RuntimeError("Cannot combine work without size")

    C = [[0 for _ in range(size)] for _ in range(size)]

    for i in range(0, worker_count):
        worker_result = get_s3_json(
            DATA_BUCKET_NAME,
            SUBMATRIX_RESULT_PATTERN.format(
                run_id=run_id,
                worker_id=i))

        for x_and_y, result in worker_result.items():
            x, y = str(x_and_y).split("#")
            C[int(x)][int(y)] = result

    store_s3_json(C, DATA_BUCKET_NAME, MATRIX_PATTERN.format(
        run_id=run_id, matrix="C"))

    return event
