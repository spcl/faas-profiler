#!/usr/bin/env python3
"""
FaaS-Profiler Post processing
"""
import networkx as nx

import os
import logging
from typing import Dict, List, Set, Tuple, Type
from uuid import UUID, uuid4
from tqdm import tqdm

from faas_profiler_core.models import (
    TracingContext,
    TraceRecord,
    InboundContext,
    OutboundContext
)
from faas_profiler_core.constants import TriggerSynchronicity
from faas_profiler_core.models import Trace, Profile

from faas_profiler.config import config
from faas_profiler.dashboard.graphing import FUNCTION_NODE, SERVICE_NODE, EDGE_SIZE_LIMIT, NODE_SIZE_LIMIT


class GraphCache:
    """
    In-Memory trace cached used for record processing.
    """

    def __init__(self) -> None:
        self._graphes_by_id: Dict[UUID, Type[nx.Graph]] = {}
        self._unique_trace_ids: Set[UUID] = set()

    def get_graph(self,
                  trace_id: UUID
                  ) -> Type[nx.DiGraph]:
        """
        Get cached graph by ID (if available)
        """
        graph = self._graphes_by_id.get(trace_id)
        if not graph:
            return

        _parent_id = graph.graph.get("parent_trace_id")
        if _parent_id:
            return self.get_graph(_parent_id)

        return graph

    def get_all_graphes(self) -> Type[Trace]:
        """
        Get all unique cached graphes
        """
        return [
            self._graphes_by_id[tid] for tid in self._unique_trace_ids]

    @property
    def number_of_graphes(self) -> int:
        """
        Returns the number of unique traces.
        """
        return len(self._unique_trace_ids)

    def cache_graph(
        self,
        trace_id: UUID,
        graph: Type[nx.DiGraph]
    ):
        """
        Caches new graph.
        """
        graph.graph["trace_id"] = str(trace_id)

        self._unique_trace_ids.add(trace_id)
        self._graphes_by_id[trace_id] = graph

    def flush_trace(self, trace_id: UUID):
        """
        Flushes trace out of unique trace IDs.
        """
        if trace_id in self._unique_trace_ids:
            self._unique_trace_ids.remove(trace_id)

    def create_or_return_graph(
        self,
        trace_id: UUID
    ) -> Type[nx.DiGraph]:
        """
        Creates or returns a graph
        """
        logger.info(f"Search for trace with ID {trace_id}")
        graph = self.get_graph(str(trace_id))
        if graph:
            logger.info(f"Found graph with ID {trace_id}")
            return graph
        else:
            logger.info(
                f"Could not find graph for ID {trace_id}. Create new graph.")
            graph = nx.DiGraph(trace_id=trace_id)
            self.cache_graph(str(trace_id), graph)
            return graph

    def state(self):

        print("ALL GRAPHES")
        for tid, graph in self._graphes_by_id.items():
            print(
                f"{tid}: GRAPH ID {graph.graph['trace_id']}, "
                "PARENT: {graph.graph.get('parent_trace_id')} {str(graph)}, MEM {hex(id(graph))}")

        print("\n UNI GRAPHES:")
        print(self._unique_trace_ids)


class RequestContextCache:

    def __init__(self) -> None:
        self._inbound_requests: Dict[
            str, Tuple[TracingContext, InboundContext]] = {}
        self._outbound_requests: Dict[
            str, Tuple[TracingContext, OutboundContext]] = {}

    def find_outbound_request_by_inbound_identifier(
        self,
        inbound_identifier: str
    ) -> Tuple[TracingContext, OutboundContext]:
        """
        Finds outbound request exists by inbound identifier
        """
        return self._outbound_requests.get(inbound_identifier)

    def find_inbound_request_by_outbound_identifier(
        self,
        outbound_identifier: str
    ) -> Tuple[TracingContext, InboundContext]:
        """
        Finds inbound request exists by outbound identifier
        """
        return self._inbound_requests.get(outbound_identifier)

    def cache_outbound_request(
        self,
        outbound_context: Type[OutboundContext],
        tracing_context: Type[TracingContext]
    ):
        """
        Caches record in outbounds
        """
        identifier_str = outbound_context.identifier_string
        if identifier_str in self._outbound_requests:
            raise RuntimeError(
                f"Identifier duplicate for {identifier_str} in outbounds")

        self._outbound_requests[identifier_str] = (
            tracing_context, outbound_context)

    def cache_inbound_request(
        self,
        inbound_context: Type[OutboundContext],
        tracing_context: Type[TracingContext]
    ):
        """
        Caches record in inbounds
        """
        identifier_str = inbound_context.identifier_string
        if identifier_str in self._inbound_requests:
            raise RuntimeError(
                f"Identifier duplicate for {identifier_str} in inbounds")

        self._inbound_requests[identifier_str] = (
            tracing_context, inbound_context)


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


def process_records() -> None:
    """
    Processes a batch of unprocessed records.
    """
    graph_cache = GraphCache()
    request_cache = RequestContextCache()

    processed_records: Dict[UUID, Type[TraceRecord]] = {}

    traces: List[Trace] = []
    profiles: Dict[str, Profile] = {}

    print(f"Processing records for {config.provider.name}")
    print(
        f"Found {len(config.storage.unprocessed_record_keys)} unprocessed records \n")

    for record in tqdm(
        config.storage.unprocessed_records(), total=len(
            config.storage.unprocessed_record_keys)):
        process_record(record, graph_cache, request_cache)
        processed_records[record.record_id] = record

    assert len(config.storage.unprocessed_record_keys) == len(
        processed_records)

    print(f"Processing {graph_cache.number_of_graphes} traces.")
    for graph in graph_cache.get_all_graphes():
        trace = Trace(graph.graph["trace_id"])

        normalized_graph_weights(graph)

        for node in nx.topological_sort(graph):
            node_id = UUID(node)
            if node_id not in processed_records:
                continue

            if trace.root_record_id is None:
                trace.root_record_id = node_id

            trace.add_record(processed_records[node_id])

        traces.append(trace)

        print(f"Saving trace {trace.trace_id}")
        config.storage.store_trace(trace)

        print(f"Saving graph {graph} for {trace.trace_id}")

        ##
        graph_data = nx.cytoscape_data(graph)

        config.storage.store_graph_data(trace.trace_id, graph_data)

        if not trace.root_record_id:
            continue

        root_record = trace.records[trace.root_record_id]
        if not root_record.function_context:
            return

        print(f"Adding trace to profile by {root_record.function_key}")
        if root_record.function_key in profiles:
            profiles[root_record.function_key].trace_ids.append(
                trace.trace_id)
        else:
            profiles[root_record.function_key] = Profile(
                profile_id=uuid4(),
                trace_ids=[trace.trace_id],
                function_context=root_record.function_context)

    print(f"Processing {len(profiles)} profiles")
    for profile in tqdm(profiles.values()):
        config.storage.store_profile(profile)

    # for g in graph_cache.get_all_graphes():
    #     pos = nx.planar_layout(g)

    #     edge_labels = dict([((u,v,), "{:.2f}".format(d['latency'])) for u,v,d in g.edges(data=True)])

    #     nx.draw(
    #         g, pos, edge_color='black', width=1, linewidths=1,
    #         node_size=500, node_color='pink', alpha=0.9,
    #         labels={node[0]: node[1].get("label") for node in g.nodes(data=True)}
    #     )
    #     nx.draw_networkx_edge_labels(
    #         g, pos,
    #         edge_labels=edge_labels,
    #         font_color='red'
    #     )
    #     plt.show()


def process_record(
    record: Type[TraceRecord],
    graph_cache: Type[GraphCache],
    request_cache: Type[RequestContextCache]
) -> None:
    """
    Process a single unprocessed record
    """
    trace_ctx = record.tracing_context
    func_ctx = record.function_context
    in_ctx = record.inbound_context

    if trace_ctx is None:
        logger.error(
            "Cannot process record without tracing context")
        return

    logger.info(
        f"Processing Record ID {trace_ctx.record_id} - Context: {trace_ctx}")

    graph: Type[nx.Graph] = graph_cache.create_or_return_graph(
        trace_id=str(trace_ctx.trace_id))

    graph.add_node(str(record.record_id), **{
        "type": FUNCTION_NODE,
        "label": record.node_label,
        "total_execution_time": func_ctx.total_execution_time,
        "handler_execution_time": func_ctx.handler_execution_time,
        "invoked_at": func_ctx.invoked_at,
        "finished_at": func_ctx.finished_at
    })

    if trace_ctx.parent_id is not None:
        attr = {
            "type": TriggerSynchronicity.SYNC.value,
            "latency": 1,
            "label": "N/A ms"
        }

        # if str(trace_ctx.parent_id) in graph:
        #     parent_node = graph.nodes[str(trace_ctx.parent_id)]
        #     latency = seconds_to_ms(
        #         time_delta_in_sec(func_ctx.invoked_at, parent_node["finished_at"]))
        #     attr["latency"] = latency
        #     attr["label"] = print_ms(latency)

        graph.add_edge(str(trace_ctx.parent_id), str(record.record_id), **attr)

    if in_ctx and in_ctx.resolvable:
        graph = resolve_inbound_context(
            record, graph, graph_cache, request_cache)

    if record.outbound_contexts:
        resolve_outbound_contexts(record, graph, graph_cache, request_cache)


def resolve_inbound_context(
    record: Type[TraceRecord],
    trace_graph: Type[nx.Graph],
    graph_cache: Type[GraphCache],
    request_cache: Type[RequestContextCache]
) -> None:
    """

    """
    if not record.inbound_context or not record.tracing_context:
        return

    identifier_str = record.inbound_context.identifier_string
    outbound_request = request_cache.find_outbound_request_by_inbound_identifier(
        identifier_str)

    if outbound_request:
        logger.info(
            f"Found Outbound request for Inbound identifier {identifier_str}")
        parent_trace_ctx, parent_out_ctx = outbound_request
        parent_graph = graph_cache.get_graph(str(parent_trace_ctx.trace_id))

        if parent_graph:
            logger.info(
                f"Found Parent graph {parent_graph} for parent tracing context {parent_trace_ctx.trace_id}")

            if parent_graph.has_edge(
                    str(parent_trace_ctx.record_id), str(record.record_id)):
                parent_graph.remove_edge(
                    str(parent_trace_ctx.record_id), str(record.record_id))

            if trace_graph.has_edge(
                    str(parent_trace_ctx.record_id), str(record.record_id)):
                trace_graph.remove_edge(
                    str(parent_trace_ctx.record_id), str(record.record_id))

            record.inbound_context.trigger_finished_at = parent_out_ctx.finished_at
            merged_graph = nx.compose(trace_graph, parent_graph)

            mid_node_id = str(uuid4())

            merged_graph.add_node(
                mid_node_id,
                **{
                    "type": SERVICE_NODE,
                    "total_execution_time": parent_out_ctx.overhead_time +
                    record.inbound_context.trigger_overhead_time,
                    "label": "{out_context}\n{in_context}".format(
                        out_context=parent_out_ctx.short_str,
                        in_context=record.inbound_context.short_str)})
            merged_graph.add_edge(str(parent_trace_ctx.record_id),
                                  mid_node_id,
                                  **{"type": parent_out_ctx.trigger_synchronicity.value,
                                     "latency": parent_out_ctx.overhead_time,
                                     "label": "{:.2f} ms".format(parent_out_ctx.overhead_time)})
            merged_graph.add_edge(mid_node_id, str(record.record_id), **{
                "type": record.inbound_context.trigger_synchronicity.value,
                "latency": record.inbound_context.trigger_overhead_time,
                "label": "{:.2f} ms".format(record.inbound_context.trigger_overhead_time)
            })

            graph_cache.cache_graph(
                parent_graph.graph["trace_id"], merged_graph)

            if trace_graph.graph["trace_id"] != merged_graph.graph["trace_id"]:
                trace_graph.graph["parent_trace_id"] = merged_graph.graph["trace_id"]

            # Forget child trace
            if parent_graph.graph["trace_id"] != trace_graph.graph["trace_id"]:
                graph_cache.flush_trace(trace_graph.graph["trace_id"])
        else:
            logger.info(
                f"Cannot find parent trace for parent trace ID {parent_trace_ctx.trace_id}")
            logger.info("Store Inbound request for later resolving.")

            request_cache.cache_inbound_request(
                record.inbound_context, record.tracing_context)
    else:
        logger.info(
            f"Cannot find Outbound request for Inbound identifier {identifier_str}")
        logger.info("Store Inbound request for later resolving.")

        request_cache.cache_inbound_request(
            record.inbound_context, record.tracing_context)

    return trace_graph


def resolve_outbound_contexts(
    record: Type[TraceRecord],
    trace_graph: Type[nx.Graph],
    graph_cache: Type[GraphCache],
    request_cache: Type[RequestContextCache]
) -> Type[GraphCache]:
    """

    """
    if not record.outbound_contexts or len(record.outbound_contexts) == 0:
        return

    for out_ctx in record.outbound_contexts:
        identifier_str = out_ctx.identifier_string
        inbound_request = request_cache.find_inbound_request_by_outbound_identifier(
            identifier_str)
        if inbound_request:
            logger.info(
                f"Found Inbound request for Outbound identifier {identifier_str}")
            child_context, child_in_ctx = inbound_request
            child_graph = graph_cache.get_graph(str(child_context.trace_id))

            if child_graph:
                logger.info(
                    f"Found Child trace {child_graph} for child tracing context {child_context.trace_id}")

                if child_graph.has_edge(str(record.record_id), str(
                        child_context.record_id)):
                    child_graph.remove_edge(
                        str(record.record_id), str(child_context.record_id))

                if trace_graph.has_edge(str(record.record_id), str(
                        child_context.record_id)):
                    trace_graph.remove_edge(
                        str(record.record_id), str(child_context.record_id))

                child_in_ctx.trigger_finished_at = out_ctx.finished_at
                merged_graph = nx.compose(child_graph, trace_graph)

                mid_node_id = str(uuid4())

                merged_graph.add_node(mid_node_id, **{
                    "type": SERVICE_NODE,
                    "total_execution_time": out_ctx.overhead_time + child_in_ctx.trigger_overhead_time,
                    "label": "{out_context}\n{in_context}".format(
                        out_context=out_ctx.short_str,
                        in_context=child_in_ctx.short_str)
                })

                merged_graph.add_edge(str(record.record_id), mid_node_id, **{
                    "type": out_ctx.trigger_synchronicity.value,
                    "latency": out_ctx.overhead_time,
                    "label": "{:.2f} ms".format(out_ctx.overhead_time)
                })
                merged_graph.add_edge(mid_node_id,
                                      str(child_context.record_id),
                                      **{"type": child_in_ctx.trigger_synchronicity.value,
                                         "latency": child_in_ctx.trigger_overhead_time,
                                         "label": "{:.2f} ms".format(child_in_ctx.trigger_overhead_time)})

                graph_cache.cache_graph(
                    trace_graph.graph["trace_id"], merged_graph)

                if child_graph.graph["trace_id"] != merged_graph.graph["trace_id"]:
                    child_graph.graph["parent_trace_id"] = merged_graph.graph["trace_id"]

                # Forget child graph
                if child_graph.graph["trace_id"] != trace_graph.graph["trace_id"]:
                    graph_cache.flush_trace(child_graph.graph["trace_id"])

                trace_graph = merged_graph
            else:
                logger.info(
                    f"Cannot find child trace for child trace ID {child_context.trace_id}")
                logger.info(
                    "Store Outbound request for later resolving.")

                request_cache.cache_outbound_request(
                    out_ctx, record.tracing_context)
        else:
            logger.info(
                f"Cannot find Inbound request for Outbound identifier {identifier_str}")
            logger.info(
                "Store Outbound request for later resolving.")

            request_cache.cache_outbound_request(
                out_ctx, record.tracing_context)


"""
Helpers
"""


def pickle_graph(G: nx.DiGraph) -> str:
    """
    Returns the path to the pickle of the graph
    """
    trace_id = G.graph["trace_id"]
    pickle_path = os.path.join(config.temporary_dir, f"{trace_id}.pkl")

    nx.write_gpickle(G, pickle_path)

    return pickle_path


def set_normalized_edge_weights(graph):
    """
    Calculates normalized edges weights.
    """
    min_size, max_size = EDGE_SIZE_LIMIT

    latencies = nx.get_edge_attributes(graph, "latency")
    if len(latencies) == 0:
        return

    max_latency = max(latencies.values())

    weights = {k: max(min_size, max_size * v * (1.0 / max_latency))
               for k, v in latencies.items()}

    nx.set_edge_attributes(graph, weights, "weight")


def set_normalized_node_weights(graph):
    """
    Calculates normalized node weights.
    """
    min_size, max_size = NODE_SIZE_LIMIT

    execution_times = nx.get_node_attributes(graph, "total_execution_time")
    if len(execution_times) == 0:
        return

    max_time = max(execution_times.values())

    weights = {k: max(min_size, max_size * v * (1.0 / max_time))
               for k, v in execution_times.items()}

    nx.set_node_attributes(graph, weights, "weight")


def normalized_graph_weights(graph):
    """
    Calculates normalized weights.
    """
    min_node, max_node = NODE_SIZE_LIMIT
    min_edge, max_edge = EDGE_SIZE_LIMIT

    execution_times = nx.get_node_attributes(graph, "total_execution_time")
    handler_times = nx.get_node_attributes(graph, "handler_execution_time")

    latencies = nx.get_edge_attributes(graph, "latency")

    max_exe_time = max(execution_times.values(), default=float('-inf'))
    max_latencies = max(latencies.values(), default=float('-inf'))
    max_time = max(max_exe_time, max_latencies)

    edge_weights = {k: max(min_edge, max_edge * v * (1.0 / max_time))
                    for k, v in latencies.items()}

    node_size = {}
    node_borders = {}
    for node, tot_time in execution_times.items():
        handler_time = handler_times.get(node, tot_time)
        profiler_time = tot_time - handler_time

        handler_frac = handler_time / tot_time
        profiler_fra = profiler_time / tot_time

        total_weight = max(min_node, max_node * tot_time * (1.0 / max_time))

        node_borders[node] = profiler_fra * total_weight
        node_size[node] = handler_frac * total_weight + node_borders[node]

    nx.set_edge_attributes(graph, edge_weights, "weight")

    nx.set_node_attributes(graph, node_size, "size")
    nx.set_node_attributes(graph, node_borders, "border")
