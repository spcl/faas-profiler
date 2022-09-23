import dash
import uuid

import dash_bootstrap_components as dbc

from typing import Type
from dash import html

from faas_profiler.config import config
from faas_profiler.models import Profile
from faas_profiler.utilis import short_uuid
from faas_profiler.dashboard.graphing import render_cytoscape_graph

from faas_profiler_core.models import Trace, TraceRecord

from .record_view import record_view

TRACE_LABEL = "{trace_id} (Invocation {no} of {trace_nos})"

TRACE_ID_KEY = "trace_id"
RECORD_ID_KEY = "record_id"

def detail_link(trace_id = "ALL", record_id = "ALL") -> str:
    return f"?{TRACE_ID_KEY}={trace_id}&{RECORD_ID_KEY}={record_id}"


def trace_menu(
    profile: Type[Profile],
    trace: Type[Trace] = None
) -> dbc.NavbarSimple:
    """
    Returns nav bar menu to select a trace within the profile.
    """
    _children = []
    if trace:
        _children.append(
            dbc.NavItem(dbc.NavLink(str(trace), href=detail_link(trace_id=trace.trace_id))))
    else:
        _children.append(
            dbc.NavItem(dbc.NavLink("View all Records", href=detail_link(trace_id="ALL"))))

    _dropdown_children = [
        dbc.DropdownMenuItem("View all Records", href=detail_link(trace_id="ALL")),
        dbc.DropdownMenuItem("Traces", header=True)]

    trace_nos = len(profile.trace_ids)
    for idx, trace_id in enumerate(profile.trace_ids):
        _dropdown_children.append(
            dbc.DropdownMenuItem(TRACE_LABEL.format(
                no=idx+1, trace_nos=trace_nos, trace_id=short_uuid(trace_id)
            ), href=detail_link(trace_id=trace_id)))

    _children.append(dbc.DropdownMenu(
        children=_dropdown_children,
        nav=True,
        in_navbar=True,
        label="Select a Trace"))

    return dbc.NavbarSimple(
        children=_children,
        brand=profile.title,
        color="secondary",
        dark=True,
        links_left=True
    )



def trace_view(
    trace: Type[Trace],
    record: Type[TraceRecord] = None
):
    """
    
    """
    root_record = trace.records[trace.root_record_id]

    try:
        trace_graph = render_cytoscape_graph(
            config.storage.get_graph_data(trace.trace_id))
    except Exception as err:
        trace_graph = html.P(f"Failed to fetch execution graph: {err}")


    def _trace_card():
        return dbc.Card([
            dbc.CardBody([
                html.H5(f"Trace {short_uuid(trace.trace_id)} of {root_record.function_key}", className="card-title"),
                html.P(
                    f"Contains {len(trace.records)} records.", className="card-text"),
                html.P(
                    "Duration: {:.2f} ms.".format(trace.duration), className="card-text"),
            ]),
        ], color="light", style={"margin-bottom": "10px"})


    def _record_selection(record):
        if record is None:
            label = "Current record selection: View all records"
        else:
            label = f"Current record selection: {record}"

        record_options = [
             dbc.DropdownMenuItem("View all records", href=detail_link(trace_id=trace.trace_id))]

        for rid, record in trace.records.items():
            record_options.append(
                dbc.DropdownMenuItem(str(record), href=detail_link(trace_id=trace.trace_id, record_id=rid)))

        return dbc.DropdownMenu(
            label=label,
            color="secondary",
            children=record_options)

    return html.Div([
        html.Div([
            html.H4("Execution Graph", className="display-8"),
            html.Div([trace_graph])
        ]),
        html.Hr(),
        _trace_card(),
        html.Hr(),
        _record_selection(record),
        html.Hr()
        # html.Div(_analyser_cards),
    ])


def profile_view_layout(
    profile_id: str = None,
    **arguments
):
    """
    Entrypoint for profile view
    """
    if profile_id is None:
        return

    profile = config.storage.get_profile(uuid.UUID(profile_id))
    trace = None
    record = None

    trace_id = arguments.get(TRACE_ID_KEY, "ALL")
    if trace_id != "ALL":
        trace = config.storage.get_trace(uuid.UUID(trace_id))

    record_id = arguments.get(RECORD_ID_KEY, "ALL")
    if trace and record_id != "ALL":
        record = trace.records.get(uuid.UUID(record_id))

    _contents = []

    if trace:
        _contents.append(trace_view(trace, record))

    if record:
        _contents.append(record_view(trace, record))

    return html.Div([
        trace_menu(profile, trace),
        dbc.Container(_contents)
    ])


dash.register_page(
    __name__,
    path_template="/profile/<profile_id>",
    layout=profile_view_layout)