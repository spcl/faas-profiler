#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash components for Index
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from dash import html
import dash_core_components as dcc

from typing import List, Type

from faas_profiler.models import TraceRecord
from faas_profiler.utilis import Loggable


class Analyzer(Loggable):
    def __init__(self):
        super().__init__()

def execution_breakdown(records: List[Type[TraceRecord]]):
    execution_times = np.array([
        r.total_execution_time for r in records])
    average_execution_time = np.average(execution_times)

    handler_execution_times = np.array([
        r.handler_execution_time for r in records])
    average_handler_time = np.average(handler_execution_times)

    outbound_execution_times = {}
    for record in records:
        if not record.outbound_contexts:
            continue

        for out_ctx in record.outbound_contexts:
            out_key = (out_ctx.provider, out_ctx.operation)
            out_time = (out_ctx.finished_at - out_ctx.invoked_at).total_seconds() * 1000

            out_total_times = outbound_execution_times.get(out_key)
            if out_total_times:
                outbound_execution_times[out_key] = np.append(out_total_times, out_time)
            else:
                outbound_execution_times[out_key] = np.array([out_time])

    outbound_execution_labels = [ f"{provider}::{operation}" for provider, operation in outbound_execution_times.keys() ]
    outbound_execution_values = [ np.average(times) for times in outbound_execution_times.values() ]

    fig =go.Figure(go.Sunburst(
        labels=["Total", "Function", "Profiler"] + outbound_execution_labels,
        parents=["", "Total", "Total", "Function", "Function", "Function", "Function"],
        values=[
            average_execution_time,
            average_handler_time,
            average_execution_time - average_handler_time,
        ] + outbound_execution_values))


    return html.Div([
        dcc.Graph(figure=fig)
    ])


def cpu_usage(records: List[Type[TraceRecord]]):
    

    record = records[0]
    cpu_usage = record.get_data_by_name("cpu::Usage")[0]

    if not cpu_usage.results:
        return

    measuring_points = cpu_usage.results.get("measuring_points")
    if not measuring_points:
        return

    timestamps = np.array([p["timestamp"] for p in measuring_points])
    usage = np.array([p["data"] for p in measuring_points])

    time = np.append(np.array([0]), np.diff(timestamps))
   
    data = pd.DataFrame({"Time": time, "Usage (%)": usage })

    fig = px.bar(data, x="Time", y="Usage (%)", title="CPU-Usage")

    return html.Div([
        dcc.Graph(figure=fig)
    ])

def mem_usage(records: List[Type[TraceRecord]]):
    

    record = records[0]
    mem_usage = record.get_data_by_name("memory::Usage")[0]

    if not mem_usage.results:
        return

    measuring_points = mem_usage.results.get("measuringPoints")
    if not measuring_points:
        return

    timestamps = np.array([p["timestamp"] for p in measuring_points])
    usage = np.array([p["data"] for p in measuring_points])
    time = np.append(np.array([0]), np.diff(timestamps))
   
    data = pd.DataFrame({"Time": time, "Usage (B)": usage })

    fig = px.line(data, x="Time", y="Usage (B)", title="Memory-Usage")

    return html.Div([
        dcc.Graph(figure=fig)
    ])


