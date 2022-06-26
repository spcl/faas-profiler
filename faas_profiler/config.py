#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from contextlib import contextmanager
from os.path import dirname, join
import yaml

PROJECT_ROOT = dirname(dirname(__file__))
TEMPLATES_ABS = join(PROJECT_ROOT, "templates")
FUNCTIONS_ABS = join(PROJECT_ROOT, "functions")
FUNCTIONS_REL = "functions"
CONFIG_DIR = join(PROJECT_ROOT, "config")


def serverless_config():
    serverless_file = join(PROJECT_ROOT, "serverless.yml")

    with open(serverless_file, "r+") as fh:
        return yaml.safe_load(fh)


@contextmanager
def update_serverless_config():
    serverless_file = join(PROJECT_ROOT, "serverless.yml")

    with open(serverless_file, "r+") as fh:
        current_config = yaml.safe_load(fh)

        yield(current_config)

        fh.seek(0)
        yaml.dump(
            current_config,
            fh,
            sort_keys=False,
            default_flow_style=False)
        fh.truncate()