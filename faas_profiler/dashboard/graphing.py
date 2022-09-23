#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for graph rendering
"""
from __future__ import annotations

import dash_cytoscape as cyto

from typing import Type

from os.path import join

from faas_profiler.models import Trace

from faas_profiler_core.constants import TriggerSynchronicity

cyto.load_extra_layouts()

FUNCTION_NODE = "function_node"
SERVICE_NODE = "service_node"

NODE_SIZE_LIMIT = (10,100)
EDGE_SIZE_LIMIT = (2, 20)

"""
Graphing
"""


# def profile_execution_graph(traces: List[Type[Trace]]):
#     """
#     Renders a execution graph for a profile
#     """
#     MAX_NODE_SIZE = 100
#     G = nx.DiGraph()

#     record_id_to_node_id = {
#         r.record_id: r.function_key for t in traces for r in t.records}

#     current_max_average_time = 0
#     for trace in traces:
#         trace_edges = set()
#         for record in trace.records:
#             _node_id = record.function_key

#             if _node_id in G:
#                 # Rolling average.
#                 node_attr = G.nodes[_node_id]
#                 num_calls = node_attr.get("number_of_executions", 1)
#                 pre_avg = node_attr.get("average_execution", 0)

#                 node_attr["number_of_executions"] = num_calls + 1
#                 node_attr["average_execution"] = pre_avg * \
#                     (num_calls - 1) / num_calls + record.execution_time / num_calls
#                 node_attr["label"] = "{} ( avg. {:.2f} ms)".format(
#                     _node_id, node_attr["average_execution"])
#             else:
#                 node_attr = dict(
#                     label="{} ( avg. {:.2f} ms)".format(
#                         _node_id,
#                         record.execution_time),
#                     type="function_node",
#                     number_of_executions=1,
#                     average_execution=record.execution_time)

#             current_max_average_time = max(
#                 current_max_average_time,
#                 node_attr["average_execution"])
#             node_attr["weight"] = node_attr["average_execution"] / \
#                 current_max_average_time * MAX_NODE_SIZE

#             G.add_node(_node_id, **node_attr)

#             _trace_ctx = record.tracing_context
#             if _trace_ctx is None or _trace_ctx.parent_id is None:
#                 continue

#             _parent_node_id = record_id_to_node_id[_trace_ctx.parent_id]
#             if G.has_edge(_parent_node_id, _node_id):
#                 edge_attr = G[_parent_node_id][_node_id]
#                 if (_parent_node_id, _node_id) not in trace_edges:
#                     edge_attr["num_taken_in_traces"] += 1
#                     edge_attr["weight"] += 1
#                     edge_attr[
#                         "label"] = f"In {edge_attr['num_taken_in_traces']} of {len(traces)} traces"

#             else:
#                 trace_edges.add((_parent_node_id, _node_id))
#                 edge_attr = dict(
#                     type="sync",
#                     num_taken_in_traces=1,
#                     label=f"In 1 of {len(traces)} traces",
#                     weight=1)

#             G.add_edge(_parent_node_id, _node_id, **edge_attr)

#     return G


def render_cytoscape_graph(data: dict):
    """
    Renders the networkx graph as cytoscape graph for Dash.
    """
    return cyto.Cytoscape(
        layout={"name": "dagre"},
        style={"width": "100%", "height": "700px"},
        elements=data["elements"],
        stylesheet=[
            {
                'selector': f'[type = "{FUNCTION_NODE}"]',
                'style': {
                    'label': 'data(label)',
                    'width': 'data(size)',
                    'height': 'data(size)',
                    "text-wrap": "wrap",
                    "background-color": "green",
                    "border-color": "darkgreen",
                    "border-width": 'data(border)'
                },
            },
            {
                'selector': f'[type = "{SERVICE_NODE}"]',
                'style': {
                    'label': 'data(label)',
                    'width': 'data(size)',
                    'height': 'data(size)',
                    "text-wrap": "wrap",
                    "background-color": "grey",
                    "shape": "rectangle"
                },
            },
            {
                'selector': f'[type = "{TriggerSynchronicity.ASYNC.value}"]',
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
                'selector': f'[type = "{TriggerSynchronicity.SYNC.value}"]',
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
            {
                'selector': 'edge',
                'style': {
                    'label': 'data(label)',
                    'line-color': '#CCCCCC',
                    'line-style': 'solid',
                    'color': '#000000',
                    'width': 'data(weight)',
                    'curve-style': 'bezier'
                }
            },
        ]
    )