#!/usr/bin/env python3
"""
FaaS-Profiler Post processing
"""

import logging
from typing import Dict, List, Set, Type
from uuid import UUID, uuid4
from tqdm import tqdm

from faas_profiler_core.models import (
    TracingContext,
    TraceRecord
)

from faas_profiler.config import config
from faas_profiler.models import Trace, Profile
from faas_profiler.core import (
    add_record_to_trace,
    add_trace_to_profile,
    get_trace_root_function,
    merge_traces
)


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


class TraceCache:
    """
    In-Memory trace cached used for record processing.
    """

    def __init__(self) -> None:
        self._traces_by_id: Dict[UUID, Trace] = {}
        self._unique_trace_ids: Set[UUID] = set()

    def get_trace(self, trace_id: UUID):
        """
        Get cached trace by ID (if available)
        """
        return self._traces_by_id.get(trace_id)

    def get_all_traces(self) -> Type[Trace]:
        """
        Get all unique cached traces
        """
        return [
            self._traces_by_id[tid] for tid in self._unique_trace_ids]

    @property
    def number_of_traces(self) -> int:
        """
        Returns the number of unique traces.
        """
        return len(self._unique_trace_ids)

    def cache_trace(self, trace: Type[Trace], override_trace_id: UUID = None):
        """
        Caches new trace.

        If override trace ID is not None, this ID will be used for the mapping.
        """
        trace_id = override_trace_id
        if trace_id is None:
            trace_id = trace.trace_id

        self._unique_trace_ids.add(trace_id)
        self._traces_by_id[trace_id] = trace

    def flush_trace(self, trace_id: UUID):
        """
        Flushes trace out of unique trace IDs.
        """
        if trace_id in self._unique_trace_ids:
            self._unique_trace_ids.remove(trace_id)


class RecordProcessor:

    @classmethod
    def execute(cls) -> List[Profile]:
        """
        Strategy for processing new records.
        """
        return cls()._execute()

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        self.trace_cache = TraceCache()
        self.inbound_requests: Dict[UUID, TracingContext] = {}
        self.outbound_requests: Dict[UUID, TracingContext] = {}

        self.profiles_by_func_key: Dict[str, Profile] = {}

    def _execute(self) -> List[Profile]:
        """
        Builds new traces out of unprocessed records
        """
        self.logger.info("Start building traces.")
        self.logger.info(
            f"Found {len(config.storage.unprocessed_record_keys)} unprocessed records \n")

        for record in tqdm(
            config.storage.unprocessed_records(), total=len(
                config.storage.unprocessed_record_keys)):
            self._process_record(record)

        self.logger.info(
            f"\n Constructed {self.trace_cache.number_of_traces} traces. Post-processing them.")
        for trace in tqdm(self.trace_cache.get_all_traces()):
            self._process_trace(trace)

        self.logger.info(
            f"\n Combined {self.trace_cache.number_of_traces} profile. Storing them.")
        for profile in tqdm(self.profiles_by_func_key.values()):
            config.storage.store_profile(profile)

        return list(self.profiles_by_func_key.values())

    def _process_record(self, record: Type[TraceRecord]) -> None:
        """
        Process on trace record.
        """
        trace_ctx = record.tracing_context
        func_ctx = record.function_context
        in_ctx = record.inbound_context
        out_ctxs = record.outbound_contexts

        if trace_ctx is None:
            self.logger.error(
                "Cannot process record without tracing context")
            return

        self.logger.info(
            f"Processing Record ID {trace_ctx.record_id} - Context: {trace_ctx} - Function Context: {func_ctx}")
        trace = self._create_or_return_trace(trace_ctx.trace_id)

        add_record_to_trace(trace, record)
        self.trace_cache.cache_trace(trace)

        if trace_ctx.parent_id is None and in_ctx.resolvable:
            self._resolve_inbound_context(trace, record)
        else:
            self.logger.info(
                "Skipping inbound resolving. Parent ID is set or inbound context is not resolvable")

        if out_ctxs:
            self.logger.info(
                f"Resolving {len(out_ctxs)} Outbound contexts.")
            self._resolve_outbound_context(trace, record)
        else:
            self.logger.info(
                "Skipping outbound resolving. No outbound contexts defined.")

        config.storage.mark_record_as_resolved(record_id=trace_ctx.record_id)

    def _process_trace(self, trace: Type[Trace]):
        """
        Postprocesses a cached trace.
        """
        root_function = get_trace_root_function(trace)
        profile = self.profiles_by_func_key.get(root_function.function_key)
        if profile:
            add_trace_to_profile(profile, trace)
        else:
            self.profiles_by_func_key[root_function.function_key] = Profile(
                profile_id=uuid4(),
                trace_ids=set([trace.trace_id]),
                function_context=root_function)

        config.storage.store_trace(trace)

    """
    Private helper Methods
    """

    def _create_or_return_trace(self, trace_id: UUID) -> Type[Trace]:
        """
        Creates or returns a trace
        """
        self.logger.info(f"Search for trace with ID {trace_id}")
        trace = self.trace_cache.get_trace(trace_id)
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
        Resolves the inbound context of record

        Child trace is the trace of the record. The goal is to find a parent trace in the outbound request mapping that triggered this record.
        If this is not found, the inbound context is saved so that it can be found in an outbound context that arrives later.
        """
        inbound_context = record.inbound_context
        tracing_context = record.tracing_context

        identifier = make_identifier_string(inbound_context.identifier)
        if identifier in self.outbound_requests:
            self.logger.info(
                f"Found Outbound request for Inbound identifier {identifier}")
            parent_context, parent_out_ctx = self.outbound_requests[identifier]
            parent_trace = self.trace_cache.get_trace(parent_context.trace_id)
            if parent_trace:
                self.logger.info(
                    f"Found Parent trace {parent_trace.trace_id} for parent tracing context {parent_context.trace_id}")

                merge_traces(parent_trace, child_trace)
                record.tracing_context.parent_id = parent_context.record_id

                inbound_context.trigger_finished_at = parent_out_ctx.finished_at

                self.trace_cache.cache_trace(
                    parent_trace, override_trace_id=child_trace.trace_id)
                self.trace_cache.flush_trace(child_trace.trace_id)
            else:
                self.logger.info(
                    f"Cannot find parent trace for parent trace ID {parent_context.trace_id}")
                self.logger.info("Store Inbound request for later resolving.")

                self.inbound_requests[identifier] = (tracing_context, inbound_context)
        else:
            self.logger.info(
                f"Cannot find Outbound request for Inbound identifier {identifier}")
            self.logger.info("Store Inbound request for later resolving.")

            self.inbound_requests[identifier] = (tracing_context, inbound_context)

    def _resolve_outbound_context(
        self,
        parent_trace: Type[Trace],
        record: Type[TraceRecord]
    ) -> None:
        """
        Resolves all outbound contexts of a record.

        Parent trace is the trace of the record. The goal is to find a child trace for all outbound contexts
        that were triggered by the outbound request.
        If this cannot be found, the context is saved so that a child trace arriving later can find it.
        """
        tracing_context = record.tracing_context

        for out_ctx in record.outbound_contexts:
            identifier = make_identifier_string(out_ctx.identifier)
            if identifier in self.inbound_requests:
                self.logger.info(
                    f"Found Inbound request for Outbound identifier {identifier}")
                child_context, child_in_ctx = self.inbound_requests[identifier]
                child_trace = self.trace_cache.get_trace(
                    child_context.trace_id)
                if child_trace:
                    self.logger.info(
                        f"Found Child trace {child_context.trace_id} for child tracing context {child_context.trace_id}")

                    child_in_ctx.trigger_finished_at = out_ctx.finished_at

                    merge_traces(parent_trace, child_trace,
                                 parent_id=tracing_context.record_id,
                                 root_child_record_id=child_context.record_id)

                    self.trace_cache.cache_trace(
                        parent_trace, override_trace_id=child_trace.trace_id)
                    self.trace_cache.flush_trace(child_trace.trace_id)
                else:
                    self.logger.info(
                        f"Cannot find child trace for child trace ID {child_context.trace_id}")
                    self.logger.info(
                        "Store Outbound request for later resolving.")

                    self.outbound_requests[identifier] = (tracing_context, out_ctx)
            else:
                self.logger.info(
                    f"Cannot find Inbound request for Outbound identifier {identifier}")
                self.logger.info(
                    "Store Outbound request for later resolving.")

                self.outbound_requests[identifier] = (tracing_context, out_ctx)
