#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contains all serverless functions
"""

from __future__ import annotations

from typing import List, Optional, Type
from uuid import UUID
from marshmallow_dataclass import dataclass
from dataclasses import field

from faas_profiler_core import models
from faas_profiler_core.constants import Provider


@dataclass
class Trace(models.BaseModel):
    """
    Represents a single trace for one function.
    """

    trace_id: UUID
    root_function_context: Optional[models.FunctionContext] = None
    # started_at: datetime
    # last_updated_at: datetime

    records: List[TraceRecord] = field(default_factory=list)

    @property
    def involved_functions(self) -> set:
        """
        Returns a set of involved functions.
        """
        return set([
            r.record_name for r in self.records])

    def get_records_by_function(self, function_key: str) -> List[Type[TraceRecord]]:
        """
        Returns all records for one function
        """
        return [
            r for r in self.records if r.function_context.function_key == function_key]


    def add_record(self, record: Type[TraceRecord]):
        """
        Adds a new record.
        """
        record.tracing_context.trace_id = self.trace_id
        self.records.append(record)

        assert record.tracing_context.trace_id == self.trace_id

    def clear_records(self) -> None:
        """
        Clears all records
        """
        self.records = []

    def merge_trace(
        self,
        child_trace: Type[Trace],
        parent_id: UUID = None,
        root_child_record_id: UUID = None
    ):
        """
        Merges child trace into this trace
        """
        for record in child_trace.records:
            record.tracing_context.trace_id = self.trace_id
            if parent_id is not None and root_child_record_id == record.tracing_context.record_id:
                record.tracing_context.parent_id = parent_id

            self.add_record(record)

        child_trace.clear_records()

    # @classmethod
    # def get_all(cls) -> List[Type[Trace]]:
    #     """
    #     Returns all traces
    #     """
    #     return [
    #         cls.load(trace) for trace in records_table.get_all_traces()
    #     ]

    # @classmethod
    # def get_by_id(cls, trace_id) -> Type[Trace]:
    #     """
    #     Returns a trace by its id.
    #     """
    #     trace_data = records_table.get_trace(str(trace_id))
    #     if not trace_data:
    #         return None

    #     return cls.load(trace_data)

    # def save(self):
    #     """
    #     Stores Trace to database
    #     """
    #     records_table.put_trace(self.dump())

    # def get_records(self) -> List[Type[TraceRecord]]:
    #     """
    #     Returns all record of the trace.
    #     """
    #     records = []
    #     for record in records_table.get_trace_records(
    #             trace_id=str(self.trace_id)):
    #         records.append(TraceRecord.load(record))

    #     return records


@dataclass
class TraceRecord(models.TraceRecord):
    """
    Represents a trace record.
    """

    def get_data_by_name(self, name: str) -> List[models.RecordData]:
        return [
            data for data in self.data if data.name == name]

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
