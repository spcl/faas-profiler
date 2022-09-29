import dash
import uuid

import dash_bootstrap_components as dbc

from typing import Type
from dash import html

from faas_profiler.config import config
from faas_profiler.utilis import short_uuid, detail_link, TRACE_ID_KEY, RECORD_ID_KEY

from faas_profiler_core.models import Trace, Profile

from .profile_view import profile_view
from .trace_view import trace_view
from .record_view import record_view

TRACE_LABEL = "{trace_id} (Invocation {no} of {trace_nos})"


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
            dbc.NavItem(
                dbc.NavLink(
                    str(trace),
                    href=detail_link(
                        trace_id=trace.trace_id))))
    else:
        _children.append(
            dbc.NavItem(
                dbc.NavLink(
                    "View all Records",
                    href=detail_link(
                        trace_id="ALL"))))

    _dropdown_children = [
        dbc.DropdownMenuItem(
            "View all Records", href=detail_link(
                trace_id="ALL")), dbc.DropdownMenuItem(
            "Traces", header=True)]

    trace_nos = len(profile.trace_ids)
    for idx, trace_id in enumerate(profile.trace_ids):
        _dropdown_children.append(
            dbc.DropdownMenuItem(TRACE_LABEL.format(
                no=idx + 1, trace_nos=trace_nos, trace_id=short_uuid(trace_id)
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


def view_layout(
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

    if not trace and not record:
        return html.Div([
            trace_menu(profile, trace),
            dbc.Container(profile_view(profile))
        ])

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
    layout=view_layout)
