#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module to generate a new serverless function to profile.
"""
from contextlib import contextmanager
from os.path import dirname, join, exists
from os import makedirs
from shutil import copyfile

import logging
import yaml

PROJECT_ROOT = dirname(dirname(__file__))
TEMPLATES_ABS = join(PROJECT_ROOT, "templates")
FUNCTIONS_ABS = join(PROJECT_ROOT, "functions")
FUNCTIONS_REL = "functions"

logger = logging.getLogger("Function Generator")

def generate(
    name: str,
    provider: str,
    runtime: str
) -> bool:
    _make_funtions_dir()

    name = name.replace(" ", "_").lower()

    func_abs_dir = join(FUNCTIONS_ABS, name)
    func_rel_dir = join(FUNCTIONS_REL, name)

    logger.info(f"Generate a new function - name: {name}, runtime: {runtime}, provider: {provider}")

    # Check if function exists
    if not exists(func_abs_dir):
        logger.info(f"CREATE: {func_abs_dir}")
        makedirs(func_abs_dir)
    else:
        logger.error(f"A function called '{name}' already exists. Abort.")
        # return False


    _copy_function_file(func_abs_dir, provider, runtime)
    _copy_dockerfile(func_abs_dir, provider, runtime)
    _copy_entry(func_abs_dir, provider, runtime)
    _register_function(name, func_rel_dir, "faas_profiler_build_image")



def _copy_function_file(function_dir, provider, runtime):
    func_file = join(function_dir, "function.py")
    logger.info(f"CREATE: {func_file}")
    copyfile(
        src=join(TEMPLATES_ABS, "aws_function_template.py"),
        dst=func_file)

def _copy_dockerfile(function_dir, provider, runtime):
    dockerfile = join(function_dir, "Dockerfile.aws")
    logger.info(f"CREATE: {dockerfile}")
    copyfile(
        src=join(TEMPLATES_ABS, "Dockerfile.template"),
        dst=dockerfile)

def _copy_entry(function_dir, provider, runtime):
    entry_file = join(function_dir, "entry.sh")
    logger.info(f"CREATE: {entry_file}")
    copyfile(
        src=join(TEMPLATES_ABS, "entry.sh"),
        dst=entry_file)


@contextmanager
def _update_serverless_config():
    serverless_file = join(PROJECT_ROOT, "serverless.yml")

    with open(serverless_file, "r+") as fh:
        current_config = yaml.safe_load(fh)

        yield(current_config)

        fh.seek(0)
        yaml.dump(current_config, fh, sort_keys=False, default_flow_style=False)
        fh.truncate()


def _register_function(name, function_relative_dir, build_image_tag):
    with _update_serverless_config() as serverless_config:
        functions = serverless_config.setdefault('functions', {})
        images = serverless_config.setdefault('provider', {}).setdefault('ecr', {}).setdefault('images', {})

        image_name = "{}_image".format(name)

        functions[name] = {
            "image": {
                "command": "function.handler",
                "entryPoint": "/entry.sh",
                "name": image_name
            }
        }

        images[image_name] = {
            "path": function_relative_dir,
            "file": "Dockerfile.aws",
            "buildArgs": {
                "BASE_IMAGE": build_image_tag,
                "FUNCTION_DIR": "/function"
            }
        }


def _make_funtions_dir():
    """
    Make functions dir on root level, if not exists
    """
    if not exists(FUNCTIONS_ABS):
        makedirs(FUNCTIONS_ABS)