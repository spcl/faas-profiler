#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash components for Index
"""
from typing import Type
import dash
from dash import html
import dash_bootstrap_components as dbc

from faas_profiler.config import config
from faas_profiler.models import Profile


def profile_card(profile: Type[Profile]) -> dbc.Card:
    _table_items = []

    _title = profile.profile_id

    _function_context = profile.function_context
    if _function_context:
        _table_items.extend([
            dbc.ListGroupItem([html.B("Provider: "), _function_context.provider.value]),
            dbc.ListGroupItem([html.B("Region: "), _function_context.region]),
            dbc.ListGroupItem([html.B("Handler: "), _function_context.handler]),
            dbc.ListGroupItem([html.B("Runtime: "), _function_context.runtime.value]),
        ])
        _title = _function_context.function_key

    return dbc.Card([
        dbc.CardBody(
            [
                html.H4([
                    str(_title),
                    dbc.Badge(f"Traces: {len(profile.trace_ids)}", className="ms-1")
                ], className="card-title"),
                dbc.ListGroup(_table_items, flush=True),
                dbc.Button("View Profile", href=f"/profile/{profile.profile_id}", color="primary"),
            ]
        ),
    ], style={"margin-bottom": "10px"})


def index():
    """
    Layout for index page.

    Shows all profiles.
    """
    if not config.storage.has_profiles:
        return html.Div(
            html.H4(
                "No recorded Profiles found.",
                className="text-danger",
                style={
                    "margin-top": "20px",
                    "text-align": "center"}))

    return dbc.Container([
        html.Div([profile_card(profile) for profile in config.storage.profiles()]),
    ], style={"margin-top": "20px"})


dash.register_page(__name__, path="/", layout=index)
