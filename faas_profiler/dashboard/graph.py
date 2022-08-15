#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for graph rendering
"""

import numpy as np
import dash_cytoscape as cyto

from typing import Type
from dash import html

from faas_profiler.models import Trace, TraceRecord
from faas_profiler.utilis import Loggable

cyto.load_extra_layouts()


class GraphRenderingError(RuntimeError):
    pass


class ExecutionGraph(Loggable):
    """
    Renders the execution graph for one trace
    """

    MAX_NODE_SIZE = 100
    DEFAULT_EXECUTION_TIME = 200
    CYPTOSCAP_STYLE = {
        "name": "circle"
    }

    def __init__(self, trace: Type[Trace], combine_records: bool = True) -> None:
        super().__init__()
        self.combine_records = combine_records
        self.trace = trace
        self.records = trace.records

        self._execution_times = self._get_execution_times()
        self._max_execution_time = np.max(self._execution_times)
        self._norm_execution_times = self._execution_times * \
            (1.0 / self._max_execution_time)

        self._nodes, self._edges = self._create_node_set()

    def nodes(self):
        """
        Returns graphs nodes
        """
        return self._nodes

    def render(self) -> Type[html.Div]:
        """
        Returns the graph.

        Caches the graph object for subsequent calls.
        """
        return cyto.Cytoscape(
            id="foo",
            layout={"name": "circle"},
            style={"width": "100%", "height": "600px"},
            elements=list(self._nodes.values()) + list(self._edges),
            stylesheet=[
                {
                    'selector': 'node',
                    'style': {
                        'label': 'data(label)',
                        'width': 'data(weight)',
                        'height': 'data(weight)',
                        "text-wrap": "wrap"
                    },
                },
                {
                    'selector': 'edge',
                    'style': {
                        'label': 'data(weight)',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#CCCCCC',
                        'source-arrow-color': '#CCCCCC',
                        'line-color': '#CCCCCC',
                        'line-style': 'dashed',
                        'mid-target-arrow-color': '#4D4D4D',
                        'mid-target-arrow-shape': 'circle',
                        'arrow-scale': 2,
                        'color': '#000000',
                        'width': 'data(weight)',
                        'curve-style': 'bezier'
                    }
                },
            ]
        )

    def _get_execution_times(self) -> np.ndarray:
        """
        Returns an array for execution time.
        """
        execution_times = np.array([r.execution_time for r in self.records])
        execution_times[execution_times is None] = 0

        return execution_times

    def _create_node_set(self) -> dict:
        """
        Creates a dict of nodes for every executed function
        """
        foo = {}

        nodes = {}
        edges = []
        for i, record in enumerate(self.records):
            tracing_ctx = record.tracing_context

            node_id = self._get_node_id_for_record(record, prefer_function_key=self.combine_records)
            foo[tracing_ctx.record_id] = node_id

            execution_time = self._execution_times[i]
            weight = self._norm_execution_times[i] * self.MAX_NODE_SIZE

            data = nodes.get(node_id, {}).get("data")
            if data:
                data["total_execution_time"] += execution_time
                data["total_weight"] += weight
                data["number_of_invocation"] += 1
                data["average_execution_time"] += data["total_execution_time"] / \
                    data["number_of_invocation"]
                data["weight"] += data["total_weight"] / \
                    data["number_of_invocation"]
            else:
                nodes[node_id] = {
                    "data": {
                        "id": node_id,
                        "label": node_id,
                        "total_execution_time": execution_time,
                        "total_weight": weight,
                        "average_execution_time": execution_time,
                        "number_of_invocation": 1,
                        "weight": weight}}

        for record in self.records:
            tracing_ctx = record.tracing_context
            if tracing_ctx.parent_id is None:
                continue

            edges.append({"data": {
                "id": f"{tracing_ctx.parent_id}#{tracing_ctx.record_id}",
                "source": foo[tracing_ctx.parent_id],
                "target": foo[tracing_ctx.record_id],
                "weight": 4.32
            }})

        return nodes, edges

    def _get_node_id_for_record(
        self,
        record: Type[TraceRecord],
        prefer_function_key: bool = True
    ):
        """
        To display a function as a node, the function key is preferred.
        """
        _func_key = None
        if record.function_context:
            _func_key = record.function_context.function_key

        _record_key = None
        if record.tracing_context:
            _record_key = str(record.tracing_context.record_id)

        if prefer_function_key and _func_key:
            return _func_key
        else:
            return _record_key
