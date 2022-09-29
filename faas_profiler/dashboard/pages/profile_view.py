import dash_bootstrap_components as dbc

from typing import Type, Dict, Any, List
from dash import html

from faas_profiler_core.models import Profile

from faas_profiler.core import group_traces_data_by_key, load_all_profile_traces
from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler.dashboard.analyzers import * # noqa

TRACE_LABEL = "{trace_id} (Invocation {no} of {trace_nos})"


def make_analyzer_cards(data: Dict[str, Any]) -> List[dbc.Card]:
    def _analyzer_card(
        header: str,
        content: str
    ) -> dbc.Card:
        return dbc.Card([
            dbc.CardBody([
                html.H5(header),
                html.Div(content)
            ])
        ], style={"margin-top": "20px"})

    _analyser_cards: List[dbc.Card] = []
    for analyzer_cls in Analyzer.__subclasses__():
        _requested_data = analyzer_cls.requested_data
        _name = analyzer_cls.safe_name()
        if _requested_data not in data:
            _analyser_cards.append(
                _analyzer_card(
                    header=_name,
                    content=f"There is no data for {_requested_data} for this profile"))
            continue

        analyzer = analyzer_cls()
        try:
            _analyser_cards.append(_analyzer_card(
                header=_name,
                content=analyzer.analyze_profile(data[_requested_data])))
        except NotImplementedError:
            pass

    return _analyser_cards


def profile_view(profile: Type[Profile]):
    profile_traces = load_all_profile_traces(profile)
    profile_data = group_traces_data_by_key(
        profile_traces, sort_by_invocation=True)

    return html.Div(make_analyzer_cards(profile_data))
