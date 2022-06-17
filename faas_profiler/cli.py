#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-profiler cli module.

Contains functionality for interacting with the profiler via command line.
"""

from faas_profiler.functions import FunctionGenerator
from faas_profiler.images import ImageManager

from subprocess import Popen, PIPE
from shlex import split
from time import sleep
from os.path import dirname, join

import logging


PROJECT_ROOT = dirname(dirname(__file__))
CONFIG_DIR = join(PROJECT_ROOT, "config")


def run_command(command, env=None):
    """
    Runs a given command in a subprocess.
    """
    command = split(command)

    process = Popen(
        command,
        stderr=PIPE,
        stdout=PIPE,
        env=env,
        text=True)

    while process.poll() is None:
        sleep(0.1)

    ret_code = process.poll()
    output, error = process.communicate()

    if ret_code != 0:
        raise RuntimeError(f"Running {command} failed: {error}")

    return output


class CLI:
    _logger = logging.getLogger("CLI")

    _BASE_BUILD_IMAGE_NAME = "fp_{}_build_image_{}-{}"
    _DOCKER_FUNCTIONS_DIR = "/function"

    @classmethod
    def _build_image_name(cls, provider, runtime, version):
        return cls._BASE_BUILD_IMAGE_NAME.format(provider, runtime, version)

    def __init__(self) -> None:
        self._image_manager = ImageManager(
            build_image_file=join(CONFIG_DIR, "build_images.yml"))

    def init(self, rebuild=False) -> None:
        self._logger.info("Building base build images for all runtimes.")
        self._image_manager.rebuild_all_images(force_rebuild=rebuild)

    def new_function(self, name, runtime):
        """
        Generates a new function by calling a FunctionGenerator
        """
        FunctionGenerator.generate(name, runtime, self._image_manager, [])
