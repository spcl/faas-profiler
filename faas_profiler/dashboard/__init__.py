#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler Dashboard module
"""

import dash
import dash_bootstrap_components as dbc

import dash_cytoscape as cyto
cyto.load_extra_layouts()

app = dash.Dash(
    external_stylesheets=[dbc.themes.FLATLY],
    use_pages=True,
    pages_folder="",
    prevent_initial_callbacks=True)

from faas_profiler.dashboard.pages.index import *
from faas_profiler.dashboard.pages.profile_view import *

app.layout = dash.html.Div([
    dbc.NavbarSimple(
        brand="FaaS Profiler Visualizer",
        brand_href="/",
        color="primary",
        dark=True
    ),
    dash.page_container])
