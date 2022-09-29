#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Information Analyzers
"""

import dash_bootstrap_components as dbc

from typing import List, Type
from dash import html

from faas_profiler_core.models import InformationOperatingSystem, InformationEnvironment
from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler_core.models import RecordData

from faas_profiler.utilis import seconds_to_ms


"""
Time Shift
"""


class TimeShiftAnalyzer(Analyzer):
    requested_data = "information::TimeShift"
    name = "Time Shift"

    UNKNOWN = "Unknown server"

    # def analyze_profile(
    #     self,
    #     traces_data: Dict[UUID, Type[RecordData]]
    # ) -> Any:
    #     df = pd.DataFrame()

    #     for trace_id, records in traces_data.items():
    #         for record in records:
    #             if not record.results:
    #                 continue

    #             _server = record.results.get("server", self.UNKNOWN)
    #             _offset = record.results.get("offset")

    #             df = df.append({
    #                 "Trace": str(trace_id),
    #                 "NTP Server": _server,
    #                 "Offset (ms)": seconds_to_ms(_offset)
    #             }, ignore_index=True)

    #     time_shift_per_trace = px.line(
    #         df.groupby(['Trace'], as_index=False).mean(),
    #         x="Trace",
    #         y='Offset (ms)',
    #         title="Time Shift Offset in ms by Trace")

    #     time_shift_per_trace.add_hline(df["Offset (ms)"].mean(), line=dict(color="Red", width=2))

    #     time_shift_per_server = px.bar(
    #         df.groupby(['NTP Server'], as_index=False).mean(),
    #         x="NTP Server",
    #         y='Offset (ms)',
    #         title="Time Shift Offset in ms by NTP Server")

    #     return html.Div(
    #         dbc.Row(
    #             [
    #                 dbc.Col(dcc.Graph(figure=time_shift_per_trace)),
    #                 dbc.Col(dcc.Graph(figure=time_shift_per_server))
    #             ]
    #         ))

    def analyze_trace(self, record_data: List[Type[RecordData]]):
        return super().analyze_trace(record_data)

    def analyze_record(self, record_data: Type[RecordData]):
        if not record_data or not record_data.results:
            return

        _results = record_data.results
        _server = _results.get("server", self.UNKNOWN)
        _offset = _results.get("offset")

        return html.Div(
            dbc.Card(
                dbc.CardBody([
                    html.H6([html.B("Server: "), _server], className="card-subtitle"),
                    html.H1("{:.2f} ms".format(seconds_to_ms(_offset)), className="display-5")
                ])
            ))


class IsWarmAnalyzer(Analyzer):
    requested_data = "information::IsWarm"
    name = "Invocations To Warm Container"

    # def analyze_profile(
    #     self,
    #     traces_data: Dict[UUID, Type[RecordData]]
    # ) -> Any:
    #     df = pd.DataFrame()

    #     for trace_id, records in traces_data.items():
    #         for record in records:
    #             if not record.results:
    #                 continue

    #             _is_warm = bool(record.results.get("is_warm"))
    #             _warm_for = record.results.get("warm_for")

    #             df = df.append({
    #                 "Trace": str(trace_id),
    #                 "Is Warm": _is_warm,
    #                 "Warm for seconds": _warm_for
    #             }, ignore_index=True)

    #     warm_for_bars = px.bar(
    #         df.groupby(['Trace'], as_index=False).mean(),
    #         x="Trace",
    #         y='Warm for seconds',
    #         title="Average Warm for seconds per Trace")

    #     warm_cold_pie = px.pie(df, names='Is Warm')

    #     return html.Div(
    #         dbc.Row(
    #             [
    #                 dbc.Col(dcc.Graph(figure=warm_cold_pie)),
    #                 dbc.Col(dcc.Graph(figure=warm_for_bars))
    #             ]
    #         ))

    def analyze_trace(self, record_data: List[Type[RecordData]]):
        return super().analyze_trace(record_data)

    def analyze_record(self, record_data: Type[RecordData]):
        if not record_data or not record_data.results:
            return

        _results = record_data.results
        _is_warm = _results.get("is_warm")
        _warm_for = _results.get("warm_for")
        _warm_since = _results.get("warm_since")

        return html.Div(
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6(html.B("Container is warm"), className="card-subtitle"),
                    html.H1(str(_is_warm), className="display-5")
                ]))),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6(html.B("Container is for (seconds)"), className="card-subtitle"),
                    html.H1("{:.2f} s".format(_warm_for), className="display-5")
                ]))),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6(html.B("Container is warm since"), className="card-subtitle"),
                    html.H4(_warm_since, className="display-7")
                ])))
            ]))


class EnvironmentAnalyzer(Analyzer):
    requested_data = "information::Environment"
    name = "Environment Information"

    def analyze_record(self, record_data: Type[RecordData]):
        if not record_data or not record_data.results:
            return

        _results = InformationEnvironment.load(record_data.results)
        _rows = [
            html.Tr([html.Td(html.B("Runtime Name")), html.Td(_results.runtime_name)]),
            html.Tr([html.Td(html.B("Runtime Version")), html.Td(_results.runtime_version)]),
            html.Tr([html.Td(html.B("Runtime Implementation")), html.Td(_results.runtime_implementation)]),
            html.Tr([html.Td(html.B("Runtime Compiler")), html.Td(_results.runtime_compiler)]),
            html.Tr([html.Td(html.B("Byte Order")), html.Td(_results.byte_order)]),
            html.Tr([html.Td(html.B("Platform")), html.Td(_results.platform)]),
            html.Tr([html.Td(html.B("Interpreter Path")), html.Td(_results.interpreter_path)]),
            html.Tr([html.Td(html.B("Installed Packages")), html.Td(
                ", ".join(_results.packages)
            )])]

        return dbc.Table(
            [html.Tbody(_rows)],
            bordered=False,
            color="light")


class OperatingSystemAnalyzer(Analyzer):
    requested_data = "information::OperatingSystem"
    name = "Operating System Information"

    def analyze_record(self, record_data: Type[RecordData]):
        if not record_data or not record_data.results:
            return

        _results = InformationOperatingSystem.load(record_data.results)
        _rows = []
        if _results.boot_time:
            _rows.append(html.Tr([html.Td(html.B("Boot Time")), html.Td(
                _results.boot_time.isoformat())]))

        if _results.system:
            _rows.append(
                html.Tr([html.Td(html.B("System")), html.Td(_results.system)]))

        if _results.node_name:
            _rows.append(
                html.Tr([html.Td(html.B("Node Name")), html.Td(_results.node_name)]))

        if _results.release:
            _rows.append(
                html.Tr([html.Td(html.B("Release")), html.Td(_results.release)]))

        if _results.machine:
            _rows.append(
                html.Tr([html.Td(html.B("Machine")), html.Td(_results.machine)]))

        return dbc.Table(
            [html.Tbody(_rows)],
            bordered=False,
            color="light")
