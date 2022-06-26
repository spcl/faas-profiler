#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, request

from .model.profile_run import ProfileRunSchema
from .storage import store_parsed_result

from .config import config

api = Blueprint('api', __name__)


@api.route("/new", methods=["POST"])
def new_results():
    try:
        profile_run = ProfileRunSchema().load(request.get_json())
    except Exception as err:
        return f"Could not parse results: {err}"

    if store_parsed_result(profile_run):
        return "", 204
    else:
        return "Could not save file", 500
