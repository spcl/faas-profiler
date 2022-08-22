#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common Analyzers
"""

import plotly.graph_objects as go

from typing import Tuple, Type
from dash import html, dcc

from faas_profiler_core.models import TraceRecord
from faas_profiler.dashboard.analyzers import Analyzer


class ExecutionTimeAnalyzer:

    def __init__(self, record: Type[TraceRecord]) -> None:
        self.record = record

    def name(self) -> str:
        return "Execution Time Breakdown"

    def render(self):
        """

        """
        _total_execution_time = self.record.execution_time
        _overhead_time = self.record.overhead_time
        _handler_time = self.record.handler_time

        if _total_execution_time is None:
            return html.P("No total execution time recorded")

        if _overhead_time is None:
            _overhead_time = 0.0

        if _handler_time is None:
            _handler_time = _total_execution_time

        outbound_labels, outbound_values = self._outbound_request_overhead()

        labels = ["Total", "Function", "Profiler"] + outbound_labels
        parents = ["", "Total", "Total"] + ["Function"] * len(outbound_labels)

        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=[
                _total_execution_time,
                _handler_time,
                _overhead_time
            ] + outbound_values))

        return html.Div([
            dcc.Graph(figure=fig)
        ])

    def _outbound_request_overhead(self) -> Tuple[list, list]:
        """
        Extracts all outbound overhead times
        """
        outbound_ctxs = self.record.outbound_contexts
        if outbound_ctxs is None or len(outbound_ctxs) == 0:
            return [], []

        labels = []
        values = []
        for i, outbound_ctx in enumerate(outbound_ctxs):
            labels.append(f"({i}) {outbound_ctx}")
            values.append(outbound_ctx.overhead_time)

        return labels, values
