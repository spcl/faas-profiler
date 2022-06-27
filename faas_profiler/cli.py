#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-profiler cli module.

Contains functionality for interacting with the profiler via command line.
"""

import logging

from subprocess import Popen, PIPE
from shlex import split
from time import sleep
from os.path import join

from faas_profiler.functions import FunctionGenerator
from faas_profiler.images import ImageManager
from faas_profiler.config import serverless_config, PROJECT_ROOT, CONFIG_DIR

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

    def profile(self, function_name: str, service: str, invocations: int = 1, redeploy: bool = False):
        func_info = self.function_info(function_name)
        if not func_info:
            self._logger.error(f"No function found with name: {function_name}")

        if not self.is_deployed(function_name):
            self._logger.warn(f"Function {function_name} is not deploy. Deploying now:")
            self.deploy_function(function_name)
        elif redeploy:
             self._logger.info(f"Redeploying function {function_name}")
             self.deploy_function(function_name)
        
        self._logger.info(f"Invoking function {function_name}")
        output = run_command(f"sls invoke --function {function_name}")

        self._logger.info(f"Function returned: {output}")


    def new_function(self, name, runtime):
        """
        Generates a new function by calling a FunctionGenerator
        """
        FunctionGenerator.generate(name, runtime, self._image_manager, [])

    def function_info(self, function_name: str) -> dict:
        sls_config = serverless_config()
        
        return sls_config.get("functions", {}).get(function_name)

    def deploy_function(self, function_name: str):
        self._logger.info(f"Deploying function {function_name}")
        run_command(f"sls deploy --function {function_name}")
        self._logger.info(f"Function {function_name} deployed")

    def is_deployed(self, function_name: str) -> bool:
        deployed_funcs = run_command("sls deploy list functions")

        return function_name in deployed_funcs and self.function_info(function_name) is not None
