#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Analyzers
"""

import pandas as pd
import numpy as np

from uuid import UUID
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
import plotly.express as px

from typing import Type, Dict, Any, List
from dash import html, dcc

from faas_profiler_core.models import S3Capture, S3AccessItem
from faas_profiler_core.models import RecordData

from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler.utilis import bytes_to_kb

class S3CaptureAnalyzer(Analyzer):
    requested_data = "aws::S3Access"
    name = "S3 Access Capture"

    def analyze_record(self, record_data: Type[RecordData]):
        if not record_data or not record_data.results:
            return

        _results = [S3Capture.load(r) for r in record_data.results]

        _bucket_cards = []
        for bucket_accesses in _results:
            _bucket_cards.append(self._make_bucket_card(bucket_accesses))

        return html.Div(_bucket_cards)


    def _make_bucket_card(self, s3_capture: Type[S3Capture]):
        print(s3_capture)

    
        _get_table = "No records"
        if s3_capture.get_objects:
            _get_table = self._make_object_table(s3_capture.get_objects)

        _create_table = "No records"
        if s3_capture.create_objects:
            _create_table = self._make_object_table(s3_capture.create_objects)

        _delete_table = "No records"
        if s3_capture.deleted_objects:
            _delete_table = self._make_object_table(s3_capture.deleted_objects)

        _head_table = "No records"
        if s3_capture.head_objects:
            _head_table = self._make_object_table(s3_capture.head_objects)

        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4([html.B("Bucket: "), s3_capture.bucket_name], className="card-title"),
                    html.H6(html.B("Get Operations"), className="card-subtitle"),
                    html.Div(_get_table),
                    html.H6(html.B("Create Operations"), className="card-subtitle"),
                    html.Div(_create_table),
                    html.H6(html.B("Delete Operations"), className="card-subtitle"),
                    html.Div(_delete_table),
                    html.H6(html.B("Head Operations"), className="card-subtitle"),
                    html.Div(_head_table)
                ]
            ), style={"margin-bottom": "20px"})

    def _make_object_table(self, s3_accesses: List[Type[S3AccessItem]]):
        header = html.Thead(
            html.Tr([
                html.Th("Object Key"),
                html.Th("Number of Accesses"),
                html.Th("Avg Execution Time")
            ]))

        rows = []
        for item in s3_accesses:
            _row = []
            _row.extend([html.Td(item.object_key), html.Td(len(item.execution_times))])

            if item.execution_times:
                _row.append(
                    html.Td("{:.2f} ms".format(np.mean(item.execution_times))))
            
            rows.append(html.Tr(_row))

        return dbc.Table([header, html.Tbody(rows)], bordered=True)
            
