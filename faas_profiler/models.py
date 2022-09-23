#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contains all serverless functions
"""
from __future__ import annotations
from datetime import datetime

from typing import Dict, List, Set, Type
from uuid import UUID, uuid4
from marshmallow_dataclass import dataclass
from dataclasses import field

from faas_profiler.utilis import short_uuid

from faas_profiler_core import models
from faas_profiler_core.constants import Provider


class ProfileView:

    def __init__(self, profile: Type[Profile]):
        self.profile = profile


        self._records_by_functions = self._create_function_view()


    @property
    def records_by_functions(self) -> Dict[str, List[TraceRecord]]:
        """
        Returns a dict of all records by functions keys
        """
        return self._records_by_functions.items()

    
    def get_records_by_function(self, function_key: str) -> List[TraceRecord]:
        """
        Returns all records for function across all traces
        """
        return self._records_by_functions.get(function_key)


    """
    Data processing
    """

    def _create_function_view(self):
        """
        Creates profile as function view.
        """
        records_by_functions = {}
      
        traces = self.profile.traces
        if traces is None or len(traces) == 0:
            return []

        for trace in traces:
            records = trace.records
            if records is None or len(records) == 0:
                continue

            for record in records:
                function_key = record.function_key
                if function_key is None:
                    continue

                records_by_functions.setdefault(function_key, []).append(record)

        return records_by_functions


@dataclass
class Profile(models.BaseModel):
    """
    Represents a single profile run, consisting of mutliple traces 
    """
    profile_id: UUID
    function_context: models.FunctionContext
    trace_ids: Set[UUID] = field(default_factory=set)


    @property
    def title(self) -> str:
        """
        Return the title of the profile
        """
        if not self.function_context:
            return str(self.profile_id)
        
        return f"{self.function_context.function_key} ({short_uuid(self.profile_id)})"

    @property
    def number_of_traces(self) -> int:
        """
        Returns the number of traces.
        """
        return len(self.traces)

@dataclass
class Trace(models.BaseModel):
    """
    Represents a single trace for one function.
    """

    trace_id: UUID
    records: Dict[UUID, TraceRecord] = field(default_factory=dict)

    root_record_id: UUID = None
    invoked_at: datetime = datetime.max
    finished_at: datetime = datetime.min

    def __str__(self) -> str:
        """
        Returns string representation of the trace.
        """
        return f"Trace: {self.trace_id} - {len(self.records)} Records"

    @property
    def duration(self) -> float:
        """
        Returns the duration in ms of the trace.
        """
        if not self.invoked_at or not self.finished_at:
            return None

        delta = self.finished_at - self.invoked_at
        return delta.total_seconds() * 1e4
    
    def add_record(self, record: Type[TraceRecord]) -> None:
        """
        Adds a record to the trace.

        Updates the tracing context to set the trace ID correctly.
        """
        trace_ctx = record.tracing_context
        func_ctx = record.function_context
        if trace_ctx:
            trace_ctx.trace_id = self.trace_id
        else:
            record.tracing_context = models.TracingContext(
                trace_id=self.trace_id, record_id=uuid4())

        if func_ctx and func_ctx.invoked_at:
            self.invoked_at = min(self.invoked_at, func_ctx.invoked_at)

        if func_ctx and func_ctx.finished_at:
            self.finished_at = max(self.finished_at, func_ctx.finished_at)

        self.records[record.tracing_context.record_id] = record


@dataclass
class TraceRecord(models.TraceRecord):
    """
    Represents a trace record.
    """

    def __str__(self) -> str:
        """
        
        """
        record_str = self.record_name

        if self.record_id:
            record_str += f" - {str(self.record_id)[:8]}"

        if self.total_execution_time:
            record_str += " - ({:.2f} ms)".format(self.total_execution_time)

        return record_str

    @property
    def function_key(self) -> str:
        """
        Returns the function key of the function context.
        """
        if self.function_context is None:
            return None

        return self.function_context.function_key

    @property
    def trace_id(self):
        """
        Returns the trace id.
        """
        if not self.tracing_context:
            return None

        return self.tracing_context.trace_id

    @property
    def record_id(self):
        """
        Returns the record id.
        """
        if not self.tracing_context:
            return None

        return self.tracing_context.record_id

    @property
    def record_name(self):
        """
        Returns the record name, composed of provider and function name
        """
        if not self.function_context:
            return f"{Provider.UNIDENTIFIED.value}::unidentified"

        func_ctx = self.function_context
        return f"{func_ctx.provider.value}::{func_ctx.function_name}"

    @property
    def total_execution_time(self) -> float:
        """
        Returns the total execution time in ms
        """
        if self.function_context is None:
            return None

        func_ctx = self.function_context
        if func_ctx.finished_at is None or func_ctx.invoked_at is None:
            return None

        delta = func_ctx.finished_at - func_ctx.invoked_at
        return delta.total_seconds() * 1000

    @property
    def handler_execution_time(self) -> float:
        """
        Returns the total execution time in ms
        """
        if self.function_context is None:
            return None

        func_ctx = self.function_context
        if func_ctx.handler_finished_at is None or func_ctx.handler_executed_at is None:
            return None

        delta = func_ctx.handler_finished_at - func_ctx.handler_executed_at
        return delta.total_seconds() * 1000
