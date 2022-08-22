#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contains all serverless functions
"""
from __future__ import annotations

from typing import Dict, List, Set, Type
from uuid import UUID
from marshmallow_dataclass import dataclass
from dataclasses import field

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
    records: List[TraceRecord] = field(default_factory=list)

    def __str__(self) -> str:
        """
        Returns string representation of the trace.
        """
        return f"Trace: {self.trace_id} - {len(self.records)} Records"

    @property
    def involved_functions(self) -> set:
        """
        Returns a set of involved functions.
        """
        return set([
            r.record_name for r in self.records])

    @property
    def root_function(self) -> Type[models.FunctionContext]:
        """
        Returns the root function context.
        """
        root_record = self.get_root_record()
        if root_record:
            return root_record.function_context
        

    def get_root_record(self) -> Type[TraceRecord]:
        """
        Returns record with no parent ID

        If multiple exists, return the record with oldest invoked at.
        """
        root_records = filter(lambda r: not r.tracing_context.parent_id, self.records)
        root_records = sorted(root_records, key=lambda r: r.function_context.invoked_at, reverse=False)

        return root_records[0]

    def get_records_by_function(self, function_key: str) -> List[Type[TraceRecord]]:
        """
        Returns all records for one function
        """
        return [
            r for r in self.records if r.function_context.function_key == function_key]



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

    def get_data_by_name(self, name: str) -> List[models.RecordData]:
        return [
            data for data in self.data if data.name == name]

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

    @property
    def is_root(self) -> bool:
        """
        Returns True if record is root
        """
        if not self.tracing_context:
            return True

        return self.tracing_context.parent_id is None
