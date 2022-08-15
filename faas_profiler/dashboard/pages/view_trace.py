#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
View trace page
"""

from typing import List, Type
import dash_bootstrap_components as dbc
import dash
from dash import html, Input, Output, dcc

from faas_profiler.models import Trace, TraceRecord

from faas_profiler.config import config
from faas_profiler.storage import RecordStorageError

from faas_profiler.dashboard.graph import ExecutionGraph, GraphRenderingError
from faas_profiler.dashboard.analyzers import execution_breakdown, cpu_usage, mem_usage

ALL_RECORDS = "All Records"

trace: Type[Trace] = None

def layout(trace_id: str = None):
    """
    Renders layout to view a trace.
    """
    if trace_id is None:
        return html.Div("No trace id provided")

    global trace, execution_graph
    try:
        trace = config.storage.get_trace(trace_id)
    except (RecordStorageError, GraphRenderingError) as err:
        return html.Div(err)

    return dbc.Container([
        html.Div([
            dbc.Checklist(
                options=[{"label": "Combine records based on function", "value": 1}],
                value=[1],
                id="combine-records",
                switch=True,
            )]),
        html.Div([
            html.H4("Execution Graph", className="display-8", style={
                "margin-top": "20px",
            }),
            html.Div(id="execution_graph")
        ]),
        html.Hr(),
        html.Div([
            html.H4("Records", className="display-8"),
            dcc.Dropdown(list(trace.involved_functions), ALL_RECORDS, id='record-selection'),
            html.Hr(),
            html.Div("records", id="records")
        ])
    ])



def view_record(records: List[Type[TraceRecord]]):

    return  html.Div([
        html.H4("Execution Breakdown", className="display-8"),
        execution_breakdown(records),
        html.H4("CPU Usage", className="display-8"),
        cpu_usage(records),
        html.H4("Memory Usage", className="display-8"),
        mem_usage(records)
    ])



@dash.callback(
    Output("records", "children"),
    Input("record-selection", "value")
)
def change_record_combination(value):
    if value == ALL_RECORDS:
        return "Show all"

    return view_record(trace.get_records_by_function(str(value)))


@dash.callback(
    Output("execution_graph", "children"),
    Input("combine-records", "value")
)
def change_execution_graph_rendering(value):
    return ExecutionGraph(trace, bool(value)).render()

dash.register_page(
    __name__,
    path_template="/trace/<trace_id>",
    layout=layout)
