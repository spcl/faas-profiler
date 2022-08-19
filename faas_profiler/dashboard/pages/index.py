#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash components for Index
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

from faas_profiler.config import config


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

    profile_ids = config.storage.profile_ids

    return dbc.Container([
        html.H3(
            f"All Profiles ({config.storage.number_of_profiles})",
            className="display-8",
            style={"margin-top": "20px"}
        ),
        html.Div([
            dbc.Card([
                dbc.CardBody(
                    [
                        html.H4(f"Profile: {profile_id}", className="card-title"),
                        html.P(
                            "Some quick example text to build on the card title and "
                            "make up the bulk of the card's content.",
                            className="card-text",
                        ),
                        dbc.Button("View Profile", href=f"/{profile_id}", color="primary"),
                    ]
                ),
            ], style={"margin-bottom": "10px"})
            for profile_id in profile_ids])
    ])


dash.register_page(__name__, path="/", layout=index)
