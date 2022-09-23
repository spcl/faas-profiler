import dash






def trace_view_layout(
    profile_id: str = None,
    trace_id: str = None
):
    """
    Entrypoint for trace view
    """
    print(profile_id)
    print(trace_id)


dash.register_page(
    __name__,
    path_template="/trace/<trace_id>/trace/<trace_id>",
    layout=trace_view_layout)