#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for graph rendering
"""
from __future__ import annotations

import numpy as np
import networkx as nx
import dash_cytoscape as cyto

from typing import List, Type

from faas_profiler.models import Trace
from faas_profiler.postprocessing import make_identifier_string

cyto.load_extra_layouts()
"""
Graphing
"""


def trace_execution_graph(trace: Type[Trace]) -> Type[nx.DiGraph]:
    """
    Create a networkx graph for one single trace.
    """
    MAX_NODE_SIZE = 100
    G = nx.DiGraph()

    all_execution_times = np.array([
        r.execution_time for r in trace.records])
    max_execution_time = np.max(all_execution_times)
    norm_execution_times = all_execution_times * \
        (1.0 / max_execution_time)

    for i, record in enumerate(trace.records):
        _record_id = record.record_id
        G.add_node(str(_record_id), **dict(
            label=str(record),
            execution_time=record.execution_time,
            handler_execution_time=record.handler_time,
            weight=norm_execution_times[i] * MAX_NODE_SIZE,
            type="function_node"
        ))

        for out_ctx in record.outbound_contexts:
            if out_ctx.has_error:
                print("Add error node")
                continue

            _out_node_id = f"{_record_id}_{make_identifier_string(out_ctx.identifier)}"
            G.add_node(_out_node_id, **dict(
                label=str(out_ctx),
                type="trigger_node",
                weight=10
            ))
            edge_label = "N/A ms"
            if out_ctx.overhead_time:
                edge_label = "{:.2f} ms".format(out_ctx.overhead_time)
            edge_weight = 10
            if out_ctx.overhead_time:
                edge_weight = out_ctx.overhead_time * 1e-3
            G.add_edge(str(_record_id), str(_out_node_id), **dict(
                label=edge_label,
                type="sync",
                weight=edge_weight
            ))

        _trace_ctx = record.tracing_context
        _in_ctx = record.inbound_context
        if not _trace_ctx or _trace_ctx.parent_id is None:
            continue

        _parent_out_node_id = str(_trace_ctx.parent_id)
        if _in_ctx:
            _parent_out_node_id += f"_{make_identifier_string(_in_ctx.identifier)}"

        edge_label = "N/A ms"
        if _in_ctx.trigger_overhead_time:
            edge_label = "{:.2f} ms".format(_in_ctx.trigger_overhead_time)
        edge_weight = 10
        if _in_ctx.trigger_overhead_time:
            edge_weight = _in_ctx.trigger_overhead_time * 1e-3
        G.add_edge(str(_parent_out_node_id), str(_record_id), **dict(
            label=edge_label,
            type="async",
            weight=edge_weight
        ))

    return G


def profile_execution_graph(traces: List[Type[Trace]]):
    """
    Renders a execution graph for a profile
    """
    MAX_NODE_SIZE = 100
    G = nx.DiGraph()

    record_id_to_node_id = {
        r.record_id: r.function_key for t in traces for r in t.records}

    current_max_average_time = 0
    for trace in traces:
        trace_edges = set()
        for record in trace.records:
            _node_id = record.function_key

            if _node_id in G:
                # Rolling average.
                node_attr = G.nodes[_node_id]
                num_calls = node_attr.get("number_of_executions", 1)
                pre_avg = node_attr.get("average_execution", 0)

                node_attr["number_of_executions"] = num_calls + 1
                node_attr["average_execution"] = pre_avg * \
                    (num_calls - 1) / num_calls + record.execution_time / num_calls
                node_attr["label"] = "{} ( avg. {:.2f} ms)".format(
                    _node_id, node_attr["average_execution"])
            else:
                node_attr = dict(
                    label="{} ( avg. {:.2f} ms)".format(
                        _node_id,
                        record.execution_time),
                    type="function_node",
                    number_of_executions=1,
                    average_execution=record.execution_time)

            current_max_average_time = max(
                current_max_average_time,
                node_attr["average_execution"])
            node_attr["weight"] = node_attr["average_execution"] / \
                current_max_average_time * MAX_NODE_SIZE

            G.add_node(_node_id, **node_attr)

            _trace_ctx = record.tracing_context
            if _trace_ctx is None or _trace_ctx.parent_id is None:
                continue

            _parent_node_id = record_id_to_node_id[_trace_ctx.parent_id]
            if G.has_edge(_parent_node_id, _node_id):
                edge_attr = G[_parent_node_id][_node_id]
                if (_parent_node_id, _node_id) not in trace_edges:
                    edge_attr["num_taken_in_traces"] += 1
                    edge_attr["weight"] += 1
                    edge_attr[
                        "label"] = f"In {edge_attr['num_taken_in_traces']} of {len(traces)} traces"

            else:
                trace_edges.add((_parent_node_id, _node_id))
                edge_attr = dict(
                    type="sync",
                    num_taken_in_traces=1,
                    label=f"In 1 of {len(traces)} traces",
                    weight=1)

            G.add_edge(_parent_node_id, _node_id, **edge_attr)

    return G


def render_cytoscape_graph(G: Type[nx.DiGraph]):
    """
    Renders the networkx graph as cytoscape graph for Dash.
    """
    return cyto.Cytoscape(
        id="foo",
        layout={"name": "dagre"},
        style={"width": "100%", "height": "600px"},
        elements=nx.cytoscape_data(G)["elements"],
        stylesheet=[
            {
                'selector': '[type = "function_node"]',
                'style': {
                    'label': 'data(label)',
                    'width': 'data(weight)',
                    'height': 'data(weight)',
                    "text-wrap": "wrap",
                    "background-color": "green"
                },
            },
            {
                'selector': '[type = "trigger_node"]',
                'style': {
                    'label': 'data(label)',
                    'width': 'data(weight)',
                    'height': 'data(weight)',
                    "text-wrap": "wrap",
                    "background-color": "blue",
                    "shape": "rectangle"
                },
            },
            {
                'selector': '[type = "async"]',
                'style': {
                    'label': 'data(label)',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': '#CCCCCC',
                    'source-arrow-color': '#CCCCCC',
                    'line-color': '#CCCCCC',
                    'line-style': 'dashed',
                    'arrow-scale': 1,
                    'color': '#000000',
                    'width': 'data(weight)',
                    'curve-style': 'bezier'
                }
            },
            {
                'selector': '[type = "sync"]',
                'style': {
                    'label': 'data(label)',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': '#CCCCCC',
                    'source-arrow-color': '#CCCCCC',
                    'line-color': '#CCCCCC',
                    'line-style': 'solid',
                    'arrow-scale': 1,
                    'color': '#000000',
                    'width': 'data(weight)',
                    'curve-style': 'bezier'
                }
            },
        ]
    )
