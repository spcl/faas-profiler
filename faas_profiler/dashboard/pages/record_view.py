import dash_bootstrap_components as dbc

from typing import Type, List, Dict, Any
from dash import html

from faas_profiler.utilis import print_ms

from faas_profiler_core.models import Trace, TraceRecord, FunctionContext
from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler.dashboard.analyzers import *

def function_context_card(
    function_context: FunctionContext
):
    _function_key_row = []
    _function_key_row.append(
        dbc.Col([html.B("Provider"), html.P(function_context.provider.name)]))
    _function_key_row.append(
        dbc.Col([html.B("Function Name"), html.P(function_context.function_name)]))
    _function_key_row.append(
        dbc.Col([html.B("Function Handler"), html.P(function_context.handler)]))

    _timing_row = []
    if function_context.total_execution_time and function_context.handler_execution_time:
        _timing_row.append(
            dbc.Col([html.B("Total Execution Time"), html.P(print_ms(function_context.total_execution_time))]))
        _timing_row.append(
            dbc.Col([html.B("Handler Execution Time"), html.P(print_ms(function_context.handler_execution_time))]))
        _timing_row.append(
            dbc.Col([html.B("Profiler Execution Time"), html.P(print_ms(function_context.profiler_time))]))

    # _arguments = None
    # if function_context.arguments:
    #     _arguments = html.Div([html.B("Arguments"), html.Code(json.dumps(function_context.arguments, indent=True))])

    _response = None
    if function_context.response:
        _response = html.Div([html.B("Response"), html.Code(str(function_context.response))])

    return dbc.Card(
        dbc.CardBody(
            [
                html.H5("Function Context", className="card-title"),
                dbc.Row(_function_key_row),
                dbc.Row(_timing_row),
                # _arguments,
                _response
            ]
        )
    )


def make_analyzer_cards(data: Dict[str, Any]) -> List[dbc.Card]:
    def _analyzer_card(
        header: str,
        content: str
    ) -> dbc.Card:
        return  dbc.Card([
            dbc.CardBody([
                html.H5(header),
                html.Div(content)
            ])
        ], style={"margin-top": "20px"})
    

    _analyser_cards: List[dbc.Card] = []
    for analyzer_cls in Analyzer.__subclasses__():
        _requested_data = analyzer_cls.requested_data
        _name = analyzer_cls.safe_name()
        if not _requested_data in data:
            _analyser_cards.append(_analyzer_card(
                header=_name,
                content=f"There is no data for {_requested_data} for this profile"))
            continue

        analyzer = analyzer_cls()    
        try:
            _analyser_cards.append(_analyzer_card(
                header=_name,
                content=analyzer.analyze_record(data[_requested_data])))
        except NotImplementedError:
            pass
        
    return _analyser_cards

def record_view(
    trace: Type[Trace],
    record: Type[TraceRecord]
):
    _contents = []

    if record.function_context:
        _contents.append(function_context_card(record.function_context))

    print(record.data.keys())
    if record.data:
        _contents = _contents + make_analyzer_cards(record.data)

    return html.Div(_contents)

