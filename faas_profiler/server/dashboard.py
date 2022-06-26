#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

from .model.profile_run import ProfileRun

dashboard = Blueprint('dashboard', __name__)


@dashboard.route("/")
def get_all_results():
    profile_runs = ProfileRun.find_all()
    return render_template('index.html', profile_runs=profile_runs)


@dashboard.route("/profile_run/<profile_run_id>")
def get_profile_run(profile_run_id):
    profile_run = ProfileRun.find(profile_run_id)

    return render_template('profile_run_view.html', profile_run=profile_run)
