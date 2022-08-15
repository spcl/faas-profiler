#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler Dashboard module
"""

import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    external_stylesheets=[dbc.themes.FLATLY],
    use_pages=True,
    pages_folder="")

from .pages import *

app.layout = dash.html.Div([
    dbc.NavbarSimple(
        brand="FaaS Profiler Visualizer",
        brand_href="/",
        color="primary",
        dark=True
    ),
    dash.page_container
])