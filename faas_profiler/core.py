"""

"""

from typing import Type
from uuid import UUID

from faas_profiler.models import Profile, Trace

from faas_profiler_core.models import TraceRecord, FunctionContext

"""
Profile methods
"""


def add_trace_to_profile(profile: Type[Profile], trace: Type[Trace]) -> None:
    """
    Adds a trace to profile
    """
    _trace_id = trace.trace_id
    if _trace_id is None:
        raise ValueError("Cannot add trace to profile without trace ID.")

    profile.trace_ids.add(_trace_id)


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
