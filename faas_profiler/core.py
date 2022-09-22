"""
Core functions
"""

import logging

from typing import List, Type
from uuid import UUID

from faas_profiler.config import config
from faas_profiler.models import Profile, Trace
from faas_profiler_core.models import TraceRecord, FunctionContext

_logger = logging.getLogger(__name__)

"""
Profile methods
"""


def load_all_profile_traces(profile: Type[Profile]) -> List[Type[Trace]]:
    """
    Loads all profile traces
    """
    traces = []
    for trace_id in profile.trace_ids:
        try:
            traces.append(config.storage.get_trace(trace_id))
        except Exception as err:
            _logger.error(f"Failed to load trace ID {trace_id}: {err}")

    return traces


"""
Trace methods
"""


def get_record_by_id(
    trace: Type[Trace],
    record_id: UUID
) -> Type[TraceRecord]:
    """
    Returns the first occurrence for record ID in given trace.
    """
    filtered_records = filter(
        lambda r: r.record_id == record_id,
        trace.records)
    try:
        return next(filtered_records)
    except StopIteration:
        return None


def group_traces_data_by_key(
    traces: List[Type[Trace]]
) -> dict:
    """
    Groups record data of multiple traces by key.
    """
    _grouped_data = {}
    for trace in traces:
        for k, data in group_record_data_by_key(trace).items():
            _grouped_trace_data = _grouped_data.setdefault(k, {})
            _grouped_trace_data.setdefault(trace.trace_id, []).extend(data)

    return _grouped_data


def group_record_data_by_key(trace: Type[Trace]) -> dict:
    """
    Groups all record data of a trace by key
    """
    _grouped_data = {}
    if not trace.records or len(trace.records) == 0:
        return _grouped_data

    for record in trace.records:
        if not record.data or len(record.data) == 0:
            continue

        for data_key, record_data in record.data.items():
            curr_data = _grouped_data.setdefault(data_key, [])
            curr_data.append(record_data)

    return _grouped_data
