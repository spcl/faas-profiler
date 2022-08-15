#!/usr/bin/env python3
"""
FaaS-Profiler Post processing
"""

import sys
import logging
from typing import Dict, Type
from uuid import UUID

from faas_profiler_core.models import TracingContext, TraceRecord

from faas_profiler.storage import S3RecordStorage
from faas_profiler.models import Trace

logging.basicConfig(stream=sys.stdout)


def make_identifier_string(identifier: dict) -> str:
    """
    Returns the identifier dict as string.
    """
    identifier = {str(k): str(v) for k, v in identifier.items()}
    identifier = sorted(
        identifier.items(),
        key=lambda x: x[0],
        reverse=False)
    identifier = map(
        lambda id: "#".join(id),
        identifier)

    return "##".join(identifier)


class Cache:

    def __init__(self) -> None:
        self.traces = {}

        self._traces_by_id = {}
        self._trace_ids = set()

    def get_trace(self, trace_id: UUID):
        return self._traces_by_id.get(trace_id)

    def get_all_traces(self) -> Type[Trace]:
        return [
            self._traces_by_id[tid] for tid in self._trace_ids]

    def store_trace(self, trace: Type[Trace], forward_trace_id: UUID = None):
        trace_id = forward_trace_id
        if trace_id is None:
            trace_id = trace.trace_id

        self._trace_ids.add(trace_id)
        self._traces_by_id[trace_id] = trace

    def remove_trace(self, trace_id: UUID):
        if trace_id in self._trace_ids:
            self._trace_ids.remove(trace_id)


class TraceBuilder:

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        self.storage = S3RecordStorage("faas-profiler-records")
        self.cache = Cache()

        self.inbound_requests: Dict[UUID, TracingContext] = {}
        self.outbound_requests: Dict[UUID, TracingContext] = {}

    def execute(self):
        """
        Builds traces based on trace records
        """
        self.logger.info("Start building traces.")
        self.logger.info(
            f"Found {len(self.storage.unprocessed_record_keys)} unprocessed records \n")

        for record in self.storage.unprocessed_records():
            trace_ctx = record.tracing_context
            func_ctx = record.function_context
            in_ctx = record.inbound_context
            out_ctxs = record.outbound_contexts

            if trace_ctx is None:
                self.logger.error(
                    "Cannot process record without tracing context")
                continue

            self.logger.info(
                f"Processing Record ID {trace_ctx.record_id} - Context: {trace_ctx} - Function Context: {func_ctx}")
            record_trace = self._create_or_return_trace(trace_ctx.trace_id)
            record_trace.add_record(record)

            self.cache.store_trace(record_trace)

            if trace_ctx.parent_id is None and in_ctx.resolvable:
                self._resolve_inbound_context(record_trace, record)
            else:
                self.logger.info(
                    "Skipping inbound resolving. Parent ID is set or inbound context is not resolvable")

            if out_ctxs:
                self.logger.info(
                    f"Resolving {len(out_ctxs)} Outbound contexts.")
                self._resolve_outbound_context(record_trace, record)
            else:
                self.logger.info(
                    "Skipping outbound resolving. No outbound contexts defined.")

        for trace in self.cache.get_all_traces():
            self.storage.upload_trace(trace)

    def _create_or_return_trace(self, trace_id: UUID) -> Type[Trace]:
        """
        Creates or returns a trace
        """
        self.logger.info(f"Search for trace with ID {trace_id}")
        trace = self.cache.get_trace(trace_id)
        if trace:
            self.logger.info(f"Found trace with ID {trace_id}")
            return trace
        else:
            self.logger.info(
                f"Could not find trace for ID {trace_id}. Create new trace.")
            return Trace(trace_id=trace_id)

    def _resolve_inbound_context(
        self,
        child_trace: Type[Trace],
        record: Type[TraceRecord]
    ) -> None:
        """

        """
        inbound_context = record.inbound_context
        tracing_context = record.tracing_context

        identifier = make_identifier_string(inbound_context.identifier)
        if identifier in self.outbound_requests:
            self.logger.info(
                f"Found Outbound request for Inbound identifier {identifier}")
            parent_context = self.outbound_requests[identifier]
            parent_trace = self.cache.get_trace(parent_context.trace_id)
            if parent_trace:
                self.logger.info(
                    f"Found Parent trace {parent_trace.trace_id} for parent tracing context {parent_context.trace_id}")

                parent_trace.merge_trace(child_trace)
                record.tracing_context.parent_id = parent_context.record_id
                self.cache.store_trace(
                    parent_trace, forward_trace_id=child_trace.trace_id)
                self.cache.remove_trace(child_trace.trace_id)
            else:
                self.logger.info(
                    f"Cannot find parent trace for parent trace ID {parent_context.trace_id}")
                self.logger.info("Store Inbound request for later resolving.")

                self.inbound_requests[identifier] = tracing_context
        else:
            self.logger.info(
                f"Cannot find Outbound request for Inbound identifier {identifier}")
            self.logger.info("Store Inbound request for later resolving.")

            self.inbound_requests[identifier] = tracing_context

    def _resolve_outbound_context(
        self,
        parent_trace: Type[Trace],
        record: Type[TraceRecord]
    ) -> None:
        """

        """
        tracing_context = record.tracing_context

        for out_ctx in record.outbound_contexts:
            identifier = make_identifier_string(out_ctx.identifier)
            if identifier in self.inbound_requests:
                self.logger.info(
                    f"Found Inbound request for Outbound identifier {identifier}")
                child_context = self.inbound_requests[identifier]
                child_trace = self.cache.get_trace(child_context.trace_id)
                if child_trace:
                    self.logger.info(
                        f"Found Child trace {child_context.trace_id} for child tracing context {child_context.trace_id}")

                    parent_trace.merge_trace(
                        child_trace,
                        parent_id=tracing_context.record_id,
                        root_child_record_id=child_context.record_id)

                    self.cache.store_trace(
                        parent_trace, forward_trace_id=child_trace.trace_id)
                    self.cache.remove_trace(child_trace.trace_id)
                else:
                    self.logger.info(
                        f"Cannot find child trace for child trace ID {child_context.trace_id}")
                    self.logger.info(
                        "Store Outbound request for later resolving.")

                    self.outbound_requests[identifier] = tracing_context
            else:
                self.logger.info(
                    f"Cannot find Inbound request for Outbound identifier {identifier}")
                self.logger.info(
                    "Store Outbound request for later resolving.")

                self.outbound_requests[identifier] = tracing_context
