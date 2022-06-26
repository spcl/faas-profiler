#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from typing import Type
from flask import current_app

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


class Config:
    def __init__(self, fp_server) -> None:
        self.fp_server = fp_server

    @property
    def is_development(self):
        return False
        return self.fp_server.env == "development"

    @property
    def local_results_path(self):
        return os.path.join(PROJECT_ROOT, ".results_store")

    @property
    def result_s3_bucket(self):
        return os.getenv("FP_SERVER_RESULT_BUCKET")

    def ensure_local_path(self):
        if not os.path.exists(self.local_results_path):
            os.mkdir(self.local_results_path)


config = Config(current_app)
