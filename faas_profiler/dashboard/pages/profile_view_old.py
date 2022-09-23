#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash page for viewing a single profile run.
"""

import dash
import dash_bootstrap_components as dbc
import logging

from typing import List, Type
from uuid import UUID
from dash import html, Output, Input, dcc, ALL
from functools import wraps

from faas_profiler_core.models import RecordData

from faas_profiler.config import config
from faas_profiler.models import Trace, Profile, TraceRecord
from faas_profiler.core import get_record_by_id, ProfileAccess

from faas_profiler.dashboard.analyzers import Analyzer
from faas_profiler.dashboard.analyzers.memory import (
    LineMemoryAnalyzer,
    MemoryUsageAnalyzer,
    ProfileMemoryUsageAnalyzer
)
from faas_profiler.dashboard.analyzers.cpu import CPUUsageAnalyzer, ProfileCPUUsageAnalyzer
from faas_profiler.dashboard.analyzers.network import NetworkIOAnalyzer, NetworkConnectionAnalyzer
from faas_profiler.dashboard.analyzers.information import (
    EnvironmentAnalyzer,
    OperatingSystemAnalyzer
)
from faas_profiler.dashboard.analyzers.disk import DiskIOAnalyzer
from faas_profiler.dashboard.analyzers.common import ExecutionTimeAnalyzer

from faas_profiler.dashboard.graphing import (
    trace_execution_graph,
    render_cytoscape_graph
)

current_profile: Type[Profile] = None
current_profile_access: List[Type[ProfileAccess]] = None
current_trace: Type[Trace] = None

_logger = logging.getLogger(__name__)

ALL_TRACES = "ALL_TRACES"
ALL_RECORDS = "ALL_RECORDS"

RECORD_DATA_ANALYZERS = {
    "network::Connections": NetworkConnectionAnalyzer,
    "network::IOCounters": NetworkIOAnalyzer,
    "memory::LineUsage": LineMemoryAnalyzer,
    "memory::Usage": MemoryUsageAnalyzer,
    "cpu::Usage": CPUUsageAnalyzer,
    "information::Environment": EnvironmentAnalyzer,
    "information::OperatingSystem": OperatingSystemAnalyzer,
    "disk::IOCounters": DiskIOAnalyzer
}


def data_analyzer_factory(
    record_data: Type[RecordData]
) -> Type[Analyzer]:
    """
    Returns a record data analzyer
    """
    _record_data_name = record_data.name
    _analyzer = RECORD_DATA_ANALYZERS.get(_record_data_name)
    if _analyzer is None:
        _logger.error(f"No data analyzer defined for {_record_data_name}")
        return None

    return _analyzer


def set_current_profile(profile_id) -> None:
    """
    Sets the current profile.
    """
    global current_profile, current_profile_access
    try:
        current_profile = config.storage.get_profile(UUID(profile_id))
        current_profile_access = ProfileAccess(current_profile)
    except Exception as err:
        _logger.error(
            f"Failed to load profile ID {profile_id}: {err}")
        current_profile = None
        current_profile_access = []


def set_current_trace(trace_id) -> None:
    """
    Sets the current trace
    """
    global current_trace
    try:
        current_trace = config.storage.get_trace(UUID(trace_id))
    except Exception as err:
        _logger.error(
            f"Failed to load trace ID {trace_id}: {err}")
        current_trace = None


def reset_current_trace() -> None:
    """
    Sets current trace to None
    """
    global current_trace
    current_trace = None


def assert_profile_loaded(func):
    """
    Decorator to assert that profile is loaded
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_profile is None:
            raise RuntimeError(
                "Function {} requires a loaded profile.".format(func.__name__))

        return func(*args, **kwargs)
    return wrapper


def assert_trace_loaded(func):
    """
    Decorator to assert that trace is loaded
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_trace is None:
            raise RuntimeError(
                "Function {} requires a loaded trace.".format(func.__name__))

        return func(*args, **kwargs)
    return wrapper


"""
Page components
"""


@assert_profile_loaded
def view_selection():
    """
    Renders a dropdown menu to select a single trace.
    """
    trace_options = [{"value": str(t_id),
                      "label": f"{i+1}: {t_id}"} for i,
                     t_id in enumerate(current_profile.trace_ids)]
    trace_options.append({"value": ALL_TRACES, "label": "View all traces"})

    return html.Div([
        dcc.Dropdown(trace_options, ALL_TRACES, id='trace-selection'),
    ], style={"margin-top": "20px"})


@assert_profile_loaded
def global_profile_information():
    """
    Returns a components for global information.
    """
    return html.Div([
        html.H4("Global Information", className="display-8")
    ])


@assert_profile_loaded
def profile_view():
    """
    Renders profile view
    """
    profile_memory = ProfileMemoryUsageAnalyzer(current_profile_access)
    profile_cpu = ProfileCPUUsageAnalyzer(current_profile_access)

    # _graph = profile_execution_graph(current_profile_access.traces)

    return html.Div([
        html.Div([
            html.H4("Execution Graph", className="display-8"),
            html.Div([render_cytoscape_graph(_graph)])
        ]),
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.H5(profile_memory.name()),
                    html.Div(profile_memory.render())
                ])
            ], style={"margin-top": "20px"}),
            dbc.Card([
                dbc.CardBody([
                    html.H5(profile_cpu.name()),
                    html.Div(profile_cpu.render())
                ])
            ], style={"margin-top": "20px"})
        ])
    ])


@assert_trace_loaded
@assert_profile_loaded
def trace_view(record: Type[TraceRecord] = None):
    """
    Renders the current trace.
    """
    record_options = [{"value": str(r.record_id), "label": str(
        r.record_id)} for r in current_trace.records]
    record_options.append({"value": ALL_RECORDS, "label": "View all records"})

    _current_selection = str(record.record_id) if record else ALL_RECORDS

    if record:
        trace_view_body = record_view(record)
    else:
        trace_view_body = "Overview"

    _graph = trace_execution_graph(current_trace)

    return html.Div([
        html.Div([
            html.H4("Execution Graph", className="display-8"),
            html.Div([render_cytoscape_graph(_graph)])
        ]),
        html.Hr(),
        dbc.Card([
            dbc.CardBody([
                html.H5(f"Trace: {current_trace.trace_id}", className="card-title"),
                html.P(
                    f"Trace contains {len(current_trace.records)} records.",
                    className="card-text",
                ),
            ]),
        ], color="light", style={"margin-bottom": "10px"}),
        dcc.Dropdown(record_options, _current_selection, id={
            'type': 'record-selection',
            'index': str(current_trace.trace_id)
        }),
        html.Div([trace_view_body])
    ])


@assert_profile_loaded
@assert_trace_loaded
def record_view(record: Type[TraceRecord]):
    """
    Renders a trace record
    """

    def record_information():
        _func_ctx = record.function_context

        card_body = []
        if _func_ctx:
            card_body.append(
                html.P([html.B("Provider: "), _func_ctx.provider.value]))
            card_body.append(
                html.P([html.B("Function name: "), _func_ctx.function_name]))
            card_body.append(
                html.P([html.B("Function handler: "), _func_ctx.handler]))

        return html.Div([
            dbc.Card([
                dbc.CardHeader(f"Record ID: {record.record_id}"),
                dbc.CardBody([
                    html.H5(f"Function: {record.function_key}", className="card-title"),
                    html.P(card_body, className="card-text")
                ]),
            ], color="light", style={"margin-bottom": "10px"})
        ], style={"margin-top": "20px"})

    def record_breakdown():
        execution_time = ExecutionTimeAnalyzer(record)
        return html.Div(
            dbc.Card([
                dbc.CardBody([
                    html.H5(execution_time.name()),
                    html.Div(execution_time.render())
                ])
            ], style={"margin-top": "20px"}))

    def record_data_cards():
        if len(record.data) == 0:
            return html.P("No record data this trace found.")

        _record_data_cards = []
        for record_data in record.data:
            analyzer_cls = data_analyzer_factory(record_data)
            if not analyzer_cls:
                continue

            analyzer = analyzer_cls(record_data)
            _record_data_cards.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(analyzer.name()),
                        html.Div(analyzer.render())
                    ])
                ], style={"margin-top": "20px"}))

        return html.Div(_record_data_cards)

    return html.Div([
        record_information(),
        record_breakdown(),
        record_data_cards()])


"""
Callback
"""


@dash.callback(
    Output("main-view", "children"),
    Input("trace-selection", "value"),
    Input({'type': 'record-selection', 'index': ALL}, 'value')
)
def change_main_view(trace_id, record_id):
    if trace_id is None or trace_id == ALL_TRACES:
        reset_current_trace()
        return profile_view()

    set_current_trace(trace_id)

    if len(record_id) == 0:
        return trace_view()

    record_id = record_id[0]
    if record_id == ALL_RECORDS:
        return trace_view()

    record = get_record_by_id(current_trace, UUID(record_id))
    if record is None:
        return html.P(f"No record found with ID {record_id}")

    return trace_view(record)


"""
Main Layout
"""


def profile_view_layout(profile_id: str = None):
    """
    Layout for view one trace.
    """
    if profile_id is None:
        return

    set_current_profile(profile_id)

    if current_profile is None:
        return html.Div(
            html.H4(
                f"Profile with ID {profile_id} not found. Please check the logs.",
                className="text-danger",
                style={
                    "margin-top": "20px",
                    "text-align": "center"}))

    return dbc.Container([
        view_selection(),
        html.Hr(),
        global_profile_information(),
        html.Hr(),

        html.Hr(),
        html.Div(id="main-view")
    ])


dash.register_page(
    __name__,
    path_template="/<profile_id>",
    layout=profile_view_layout)
