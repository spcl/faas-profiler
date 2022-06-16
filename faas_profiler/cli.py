#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-profiler cli module.

Contains functionality for interacting with the profiler via command line.
"""

from faas_profiler import function_generator

from contextlib import contextmanager
from subprocess import Popen, PIPE
from shlex import split
from time import sleep
from os.path import dirname, join, exists
from os import makedirs
from shutil import copyfile

import logging
import yaml
import docker



PROJECT_ROOT = dirname(dirname(__file__))

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

    
    _GENERATORS = {
        "function": function_generator.generate
    }
    _DOCKER_FUNCTIONS_DIR = "/function"
    _DOCKER_BUILD_IMAGE_NAME = "faas_profiler_build_image"


    def __init__(self) -> None:
        self._docker = docker.from_env()
        self._build_image = self._docker.images.get(self._DOCKER_BUILD_IMAGE_NAME)

        self._functions = {}


    def build_base_image(self, dockerfile=None, tag=None):
        """
        (Re-)Builds the FaaS-Profiler docker build image.
        """
        if not dockerfile:
            dockerfile = join(PROJECT_ROOT, "docker", "aws", "Dockerfile.build")

        self._logger.info(f"Rebuilding profiler base image: {dockerfile}")

        self._build_image = self._docker.images.build(
            tag=tag if tag else self._DOCKER_BUILD_IMAGE_NAME,
            path=".",
            dockerfile=dockerfile,
            buildargs={
                'FUNCTION_DIR': self._DOCKER_FUNCTIONS_DIR
            },
            quiet=False)


    #     if self._GENERATORS[generator](*args, **kwargs, build_image=self._build_image, docker_function_dir=self._DOCKER_FUNCTIONS_DIR):
    #         self._logger.info("Generation successful.")


    def new_function(self, name):
        function_generator.generate(name, "aws", "python")