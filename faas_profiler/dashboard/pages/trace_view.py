import dash_bootstrap_components as dbc

from typing import Type, List, Dict, Any
from dash import html

from faas_profiler.dashboard.graphing import render_cytoscape_graph
from faas_profiler.config import config
from faas_profiler.utilis import short_uuid, detail_link
from faas_profiler.core import group_record_data_by_key

from faas_profiler_core.models import Trace, TraceRecord
from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler.dashboard.analyzers import * # noqa


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
                content=analyzer.analyze_trace(data[_requested_data])))
        except NotImplementedError:
            pass

    return _analyser_cards


def trace_analyzers(trace: Type[Trace]):
    data = group_record_data_by_key(trace, sort_by_invocation=True)

    return html.Div(make_analyzer_cards(data))


def trace_view(
    trace: Type[Trace],
    record: Type[TraceRecord] = None
):
    """

    """
    root_record = trace.records[trace.root_record_id]

    try:
        trace_graph = render_cytoscape_graph(
            config.storage.get_graph_data(trace.trace_id))
    except Exception as err:
        trace_graph = html.P(f"Failed to fetch execution graph: {err}")

    def _trace_card():
        return dbc.Card([
            dbc.CardBody([
                html.H5(f"Trace {short_uuid(trace.trace_id)} of {root_record.function_key}", className="card-title"),
                html.P(
                    f"Contains {len(trace.records)} records.", className="card-text"),
                html.P(
                    "Duration: {:.2f} ms.".format(trace.duration), className="card-text"),
            ]),
        ], color="light", style={"margin-bottom": "10px"})

    def _record_selection(record):
        if record is None:
            label = "Current record selection: View all records"
        else:
            label = f"Current record selection: {record}"

        record_options = [
            dbc.DropdownMenuItem(
                "View all records",
                href=detail_link(
                    trace_id=trace.trace_id))]

        for rid, record in trace.records.items():
            record_options.append(
                dbc.DropdownMenuItem(
                    str(record),
                    href=detail_link(
                        trace_id=trace.trace_id,
                        record_id=rid)))

        return dbc.DropdownMenu(
            label=label,
            color="secondary",
            children=record_options)

    trace_analyzers_card = None
    if record is None:
        trace_analyzers_card = trace_analyzers(trace)

    return html.Div([
        html.Div([
            html.H4("Execution Graph", className="display-8"),
            html.Div([trace_graph])
        ]),
        html.Hr(),
        _trace_card(),
        html.Hr(),
        _record_selection(record),
        html.Hr(),
        trace_analyzers_card
    ])
