

from collections import namedtuple
from dataclasses import dataclass
from email import header, message
import dash
import dash_bootstrap_components as dbc
import logging

from typing import Any, List, Type
from uuid import UUID
from dash import html, Output, Input, dcc, ALL
from functools import wraps

from faas_profiler.config import config
from faas_profiler.dashboard import analyzers
from faas_profiler.models import Profile, Trace, TraceRecord
from faas_profiler.core import (
    get_record_by_id,
    load_all_profile_traces,
    group_traces_data_by_key,
    group_record_data_by_key
)

from faas_profiler.dashboard.graphing import (
    trace_execution_graph,
    render_cytoscape_graph
)

from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler.dashboard.analyzers import *

ALL_TRACES = "ALL_TRACES"
ALL_RECORDS = "ALL_RECORDS"

"""
State
"""

@dataclass
class ViewState:
    profile: Type[Profile] = None
    trace: Type[Trace] = None

state: Type[ViewState] = ViewState()


CACHED_ANALYSER_CARDS = {}

def update_state(
    profile_id: str = None,
    trace_id: str = None,
) -> None:
    """
    Update current state
    """
    global state

    def _get_profile() -> Type[Profile]:
        if not profile_id:
            return state.profile

        try:
            _profile_id = profile_id if isinstance(profile_id, UUID) else UUID(profile_id)
            if state.profile and state.profile.profile_id == _profile_id:
                return state.profile

            return config.storage.get_profile(_profile_id)
        except Exception as err:
            print(err)
            return state.profile

    def _get_trace() -> Type[Trace]:
        if not trace_id:
            return state.trace
        
        try:
            _trace_id = UUID(trace_id)
            if state.trace and state.trace.trace_id == _trace_id:
                return state.trace

            return config.storage.get_trace(_trace_id)
        except Exception as err:
            print(err)
            return state.trace


    state.profile = _get_profile()
    state.trace = _get_trace()


def make_analyzer_cards(
    cache_key: Any,
    data: Dict[str, Any],
    analyzer_method: str
) -> List[dbc.Card]:
    global CACHED_ANALYSER_CARDS

    if cache_key in CACHED_ANALYSER_CARDS:
        return CACHED_ANALYSER_CARDS[cache_key]

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
                content=getattr(analyzer, analyzer_method)(data[_requested_data])))
        except NotImplementedError:
            pass

    CACHED_ANALYSER_CARDS[cache_key] = _analyser_cards
        
    return _analyser_cards

"""
Components
"""

def profile_information():
    _profile = state.profile

    _title = _profile.profile_id
    if _profile.function_context:
        _title = _profile.function_context.function_key
    
    def _trace_option_label(idx, trace_id):
        return "Invocation {no} of {trace_nos} - TraceID: {trace_id}".format(
            no=idx+1, trace_nos=len(_profile.trace_ids), trace_id=str(trace_id))

    trace_options = [{
        "value": str(t_id),
        "label": _trace_option_label(i, t_id)
    } for i, t_id in enumerate(_profile.trace_ids)]
    trace_options.append({"value": ALL_TRACES, "label": "View all traces"})

    return dbc.Container(
            [
                html.H1(_title, className="display-6"),
                html.Div([
                    dbc.Badge(str(state.profile.profile_id), className="ms-1")
                ]),
                html.Hr(className="my-2"),
                html.Div([
                    dcc.Dropdown(trace_options, ALL_TRACES, id='trace-selection'),
                ])
            ],
            fluid=True,
            className="py-3")


def trace_information():
    _trace = state.trace
    return dbc.Card([
        dbc.CardBody([
            html.H5(f"Trace: {_trace.trace_id}", className="card-title"),
            html.P(
                f"Trace contains {len(_trace.records)} records.",
                className="card-text",
            ),
        ]),
    ], color="light", style={"margin-bottom": "10px"})

def record_information(record: Type[TraceRecord] = None):
    if record is None:
        return
    
    return html.Div("Record!")

"""
Page Views
"""

def profile_view():
    # _profile_traces = load_all_profile_traces(state.profile)
    # _traces_data = group_traces_data_by_key(_profile_traces)

    # _analyser_cards = make_analyzer_cards(
    #     cache_key=state.profile.profile_id,
    #     data=_traces_data,
    #     analyzer_method="analyze_profile")

    return dbc.Container([
        html.Div("Foo")
    ])


def trace_view(record: Type[TraceRecord] = None):
    _trace = state.trace

    # record_options = [{"value": str(rid), "label": str(r)} for rid, r in _trace.records.items()]
    # record_options.append({"value": ALL_RECORDS, "label": "View all records"})

    # _current_selection = str(record.record_id) if record else ALL_RECORDS

    # if record:
    #     trace_view_body = record_view(record)
    # else:
    #     trace_view_body = "Overview"

    _graph = trace_execution_graph(state.trace)
    _cyto = render_cytoscape_graph(_graph)

    breakpoint()

    # _analyser_cards = []
    # if record:
    #     print(record.data)
    #     _analyser_cards = make_analyzer_cards(
    #         cache_key=record.record_id,
    #         data=record.data,
    #         analyzer_method="analyze_record")
    # else:
    #     _trace_data = group_record_data_by_key(_trace)
    #     _analyser_cards = make_analyzer_cards(
    #         cache_key=_trace.trace_id,
    #         data=_trace_data,
    #         analyzer_method="analyze_trace")


    return html.Div([
        html.Div([
            html.H4("Execution Graph", className="display-8"),
            html.Div([_cyto])
        ]),
        # html.Hr(),
        # trace_information(),
        # dcc.Dropdown(record_options, _current_selection, id={
        #     'type': 'record-selection',
        #     'index': str(_trace.trace_id)
        # }),
        # record_information(record),
        # html.Div(_analyser_cards),
    ])


def record_view(record):
    return "View Record"


"""
Change View
"""

# @dash.callback(
#     Output("main-view", "children"),
#     Input("trace-selection", "value"),
#     Input({'type': 'record-selection', 'index': ALL}, 'value')
# )
# def change_main_view(trace_id, record_id):
#     # Remove ME
#     if trace_id is None or trace_id == ALL_TRACES:
#         update_state(
#             profile_id=state.profile.profile_id,
#             trace_id=None)

#         return profile_view()

#     update_state(
#         profile_id=state.profile.profile_id,
#         trace_id=trace_id)

#     if len(record_id) == 0:
#         return trace_view()

#     record_id = record_id[0]
#     if record_id == ALL_RECORDS:
#         return trace_view()

#     record = get_record_by_id(state.trace, UUID(record_id))
#     if record is None:
#         return html.P(f"No record found with ID {record_id}")

#     return trace_view(record)

"""
Main entry
"""

def view_layout(profile_id: str = None):
    """
    Main layout to view a profile
    """

    data = config.storage.get_graph_picke("7c3a50f8-4f2a-448b-88b8-825aff11421e")
    _cyto = render_cytoscape_graph(data)

    return html.Div([
        _cyto
    ])

    # if profile_id is None:
    #     return

    # update_state(profile_id=profile_id)

    # if current_profile is None:
    #     return html.Div(
    #         html.H4(
    #             f"Profile with ID {profile_id} not found. Please check the logs.",
    #             className="text-danger",
    #             style={
    #                 "margin-top": "20px",
    #                 "text-align": "center"}))

    # return dbc.Container([
    #     profile_information(),
    #     # html.Hr(),
    #     # global_profile_information(),
    #     # html.Hr(),

    #     html.Hr(),
    #     html.Div(id="main-view")
    # ])

dash.register_page(
    __name__,
    path_template="/<profile_id>",
    layout=view_layout)