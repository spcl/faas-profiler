#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Information Analyzers
"""

import dash_bootstrap_components as dbc

from typing import Type
from dash import html

from faas_profiler_core.models import InformationOperatingSystem, InformationEnvironment
from faas_profiler.dashboard.analyzers import Analyzer
from faas_profiler_core.models import RecordData


class EnvironmentAnalyzer(Analyzer):

    def __init__(self, record_data: Type[RecordData]):
        self.record_data = record_data
        self.record_name = record_data.name
        self.results = InformationEnvironment.load(self.record_data.results)

        super().__init__(record_data)

    def name(self) -> str:
        """
        Returns the name for operating system information
        """
        return "Environment Information"

    def render(self):
        """
        Returns a table for environment information
        """
        _rows = [
            html.Tr([html.Td(html.B("Runtime Name")), html.Td(self.results.runtime_name)]),
            html.Tr([html.Td(html.B("Runtime Version")), html.Td(self.results.runtime_version)]),
            html.Tr([html.Td(html.B("Runtime Implementation")), html.Td(self.results.runtime_implementation)]),
            html.Tr([html.Td(html.B("Runtime Compiler")), html.Td(self.results.runtime_compiler)]),
            html.Tr([html.Td(html.B("Byte Order")), html.Td(self.results.byte_order)]),
            html.Tr([html.Td(html.B("Platform")), html.Td(self.results.platform)]),
            html.Tr([html.Td(html.B("Interpreter Path")), html.Td(self.results.interpreter_path)]),
            html.Tr([html.Td(html.B("Installed Packages")), html.Td(
                ", ".join(self.results.packages)
            )])]

        return dbc.Table(
            [html.Tbody(_rows)],
            bordered=False,
            color="light")


class OperatingSystemAnalyzer(Analyzer):

    def __init__(self, record_data: Type[RecordData]):
        self.record_data = record_data
        self.record_name = record_data.name
        self.results = InformationOperatingSystem.load(
            self.record_data.results)

        super().__init__(record_data)

    def name(self) -> str:
        """
        Returns the name for operating system information
        """
        return "Operating System Information"

    def render(self):
        """
        Returns a table for operating system information
        """
        _rows = []
        if self.results.boot_time:
            _rows.append(html.Tr([html.Td(html.B("Boot Time")), html.Td(
                self.results.boot_time.isoformat())]))

        if self.results.system:
            _rows.append(
                html.Tr([html.Td(html.B("System")), html.Td(self.results.system)]))

        if self.results.node_name:
            _rows.append(
                html.Tr([html.Td(html.B("Node Name")), html.Td(self.results.node_name)]))

        if self.results.release:
            _rows.append(
                html.Tr([html.Td(html.B("Release")), html.Td(self.results.release)]))

        if self.results.machine:
            _rows.append(
                html.Tr([html.Td(html.B("Machine")), html.Td(self.results.machine)]))

        return dbc.Table(
            [html.Tbody(_rows)],
            bordered=False,
            color="light")
