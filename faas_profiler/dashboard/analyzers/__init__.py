#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash components for Index
"""
from faas_profiler.utilis import Loggable


class Analyzer(Loggable):

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        """
        Returns the analyzer name.
        """
        pass

    def render(self):
        """
        Renders the analyzers
        """
        pass
