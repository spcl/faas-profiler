#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU Analyzers
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import dash_bootstrap_components as dbc
from typing import Type, Dict
from dash import html, dcc

from faas_profiler_core.models import CPUUsage, CPUCoreUsage

from faas_profiler.utilis import seconds_to_ms
from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler_core.models import RecordData


class CPUUsageAnalyzer(Analyzer):
    requested_data = "cpu::UsageOverTime"
    name = "CPU Usage Over Time"

    X_AXIS = "Time ({unit})"
    Y_AXIS = "Usage ({unit})"

    def analyze_record(self, record_data: Type[RecordData]):
        """
        Returns a line chart for all recorded memory usages.
        """
        results = CPUUsage.load(record_data.results)
        times, usage = zip(*results.percentage)

        interval = seconds_to_ms(np.array(times) - times[0])
        usage = np.array(usage)

        data = pd.DataFrame({
            self.X_AXIS.format(unit="ms"): interval,
            self.Y_AXIS.format(unit="%"): usage
        })

        fig = px.line(
            data,
            x=self.X_AXIS.format(unit="ms"),
            y=self.Y_AXIS.format(unit="%"),
            title="CPU-Usage")

        fig.add_trace(go.Scatter(
            x=interval,
            y=np.repeat(np.mean(usage), len(usage)),
            name="Mean",
            line=dict(color="Red", width=2)))

        return html.Div([
            dcc.Graph(figure=fig),
            dbc.Row(
                [
                    dbc.Col([html.B("Number of Measuring Points:"), html.P(len(interval))]),
                    dbc.Col([html.B("Interval:"), html.P(f"{seconds_to_ms(results.interval)} ms")])
                ]
            )
        ])

    def analyze_trace(
        self,
        record_data: Dict[str, Type[RecordData]]
    ):
        df = pd.DataFrame()
        fig = go.Figure()

        for record_id, data in record_data.items():
            results = CPUUsage.load(data.results)
            times, usage = zip(*results.percentage)

            interval = np.array(times) - times[0]
            usage = np.array(usage)

            record_frame = pd.DataFrame({
                "Time (ms)": seconds_to_ms(interval),
                "Usage (%)": usage,
                "Record ID": str(record_id)
            })
            df = pd.concat([df, record_frame])

        fig = px.line(
            df,
            title="CPU Usage by Record",
            x="Time (ms)",
            y="Usage (%)",
            color="Record ID")

        return html.Div([
            dcc.Graph(figure=fig)
        ])

    def analyze_profile(self, traces_data):
        df = pd.DataFrame()
        for idx, (trace_id, trace_data) in enumerate(traces_data.items()):

            trace_usage = []
            for record_data in trace_data.values():
                record_result = CPUUsage.load(record_data.results)
                _, usage = zip(*record_result.percentage)
                trace_usage += usage

            df = pd.concat([df, pd.DataFrame({
                "Trace ID": str(trace_id)[:8],
                "Average Usage": np.array(trace_usage).mean()
            }, index=[idx])])

        fig = px.line(
            df,
            x="Trace ID",
            y="Average Usage",
            title="CPU-Usage")

        return html.Div([
            dcc.Graph(figure=fig)
        ])


class CPUCoreUsageAnalyzer(Analyzer):
    requested_data = "cpu::UsageByCores"
    name = "CPU Usage Core"

    X_AXIS = "Time ({unit})"
    Y_AXIS = "Usage ({unit})"

    def analyze_record(self, record_data: Type[RecordData]):
        """
        Returns a line chart for all recorded memory usages.
        """
        df = pd.DataFrame()
        results = CPUCoreUsage.load(record_data.results)

        for core, core_percentages in results.percentage.items():
            times, usage = zip(*core_percentages)
            df = pd.concat([df, pd.DataFrame({
                "Core": f"Core {core}",
                "Time (ms)": seconds_to_ms(np.array(times) - times[0]),
                "Usage (%)": np.array(usage)
            })])

        fig = px.line(
            df,
            title="CPU Usage by Record",
            x="Time (ms)",
            y="Usage (%)",
            color="Core")

        return html.Div([
            dcc.Graph(figure=fig)
        ])

    def analyze_trace(
        self,
        record_data: Dict[str, Type[RecordData]]
    ):
        df = pd.DataFrame()

        for record_id, data in record_data.items():
            results = CPUCoreUsage.load(data.results)
            for core, core_percentages in results.percentage.items():
                times, usage = zip(*core_percentages)
                df = pd.concat([df, pd.DataFrame({
                    "Core": f"Core {core}",
                    "Time (ms)": seconds_to_ms(np.array(times) - times[0]),
                    "Usage (%)": np.array(usage),
                    "Record ID": str(record_id)
                })])

        fig = px.line(
            df,
            title="CPU Usage by Record",
            x="Time (ms)",
            y="Usage (%)",
            color="Record ID",
            symbol="Core")

        return html.Div([
            dcc.Graph(figure=fig)
        ])
