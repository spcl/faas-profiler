"""

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


class ProfileAccess:

    def __init__(self, profile: Type[Profile]) -> None:
        self.profile = profile
        self.traces = load_all_profile_traces(profile)

        self._group_data = None

    def get_all_record_data(self, data_name: str):
        """
        Returns all record data for one name
        """
        if self._group_data is None:
            self._group_data = self._group_data_by_name()

        return self._group_data.get(data_name, [])

    def _group_data_by_name(self):
        """
        Groups all trace data by record data key.
        """
        grouped_data = {}

        for trace in self.traces:
            for record in trace.records:
                for record_data in record.data:
                    grouped_records = grouped_data.setdefault(
                        record_data.name, {})
                    grouped_traces = grouped_records.setdefault(
                        trace.trace_id, {})

                    grouped_traces[str(record)] = record_data.results

        return grouped_data


def add_trace_to_profile(profile: Type[Profile], trace: Type[Trace]) -> None:
    """
    Adds a trace to profile
    """
    _trace_id = trace.trace_id
    if _trace_id is None:
        raise ValueError("Cannot add trace to profile without trace ID.")

    profile.trace_ids.add(_trace_id)


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


def clear_trace_records(trace: Type[Trace]):
    """
    Resets all records for trace.
    """
    trace.records = []


def add_record_to_trace(trace: Type[Trace], record: Type[TraceRecord]):
    """
    Adds record to trace.

    Makes sure that trace id of record is the same than the trace
    """
    record.tracing_context.trace_id = trace.trace_id
    trace.records.append(record)

    assert record.tracing_context.trace_id == trace.trace_id


def merge_traces(
    parent_trace: Type[Trace],
    child_trace: Type[Trace],
    parent_id: UUID = None,
    root_child_record_id: UUID = None
) -> None:
    """
    Merges child trace into parent.

    Complexity: O(num_of_child_records)
    """
    for record in child_trace.records:
        record.tracing_context.trace_id = parent_trace.trace_id
        if parent_id is not None and root_child_record_id == record.tracing_context.record_id:
            record.tracing_context.parent_id = parent_id

        add_record_to_trace(parent_trace, record)

    clear_trace_records(child_trace)


def get_trace_root_record(trace: Type[Trace]) -> Type[TraceRecord]:
    """
    Returns record with no parent ID.
    Returns None if no records exists.

    If multiple exists, return the record with oldest invoked at.
    """
    if not trace.records or len(trace.records) == 0:
        return None

    root_records = filter(
        lambda r: not r.tracing_context.parent_id,
        trace.records)
    root_records = sorted(
        root_records,
        key=lambda r: r.function_context.invoked_at,
        reverse=False)

    return root_records[0]


def get_trace_root_function(trace: Type[Trace]) -> Type[FunctionContext]:
    """
    Returns the function context of the root record.

    Return None if no root function exists or the function has no function
    """
    root_record = get_trace_root_record(trace)
    if root_record and root_record.function_context:
        return root_record.function_context

    return None


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
