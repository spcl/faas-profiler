#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash components for Index
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

from faas_profiler.config import config

def trace_list():
    """
    Renders a trace list for all recorded traces
    """
    if len(config.storage.trace_keys) == 0:
        return html.Div(
            html.H4(
                "No recorded Traces found.",
                className="text-danger",
                style={
                    "margin-top": "20px",
                    "text-align": "center"}))

    return html.Div(
        dbc.Accordion(children=[
            dbc.AccordionItem([
                dbc.Button(
                    "View Trace",
                    href=f"/trace/{trace.trace_id}",
                    outline=True,
                    color="primary"),
            ],
                # title=f"Trace ID: {trace.trace_id} - Function Name: {trace.root_function_context.function_name}"
                title=f"Trace ID: {trace.trace_id}"
            ) for trace in config.storage.traces()],
            flush=True,
            start_collapsed=True
        )
    )


def layout():
    """
    Layout for index page.

    Shows all traces.
    """

    return dbc.Container([
        html.H3(
            f"Recorded Traces ({config.storage.number_of_traces})",
            className="display-8",
            style={"margin-top": "20px"}
        ),
        html.Hr(className="my-2"),
        html.P(
            "Look at traces recorded with the Faas Profiler.",
            className="lead",
        ),
        trace_list()
    ])


dash.register_page(__name__, path='/', layout=layout)
