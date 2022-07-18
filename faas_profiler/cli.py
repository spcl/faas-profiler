#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-profiler cli module.
"""

import click

from subprocess import Popen, PIPE
from shlex import split
from time import sleep
from termcolor import cprint, colored
from inquirer import List, Confirm, prompt


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


ERROR_COLOR = 'red'
SUCCESS_COLOR = 'green'
ASK_COLOR = 'yellow'


def out(
    message: str,
    color: str = None,
    highlight: str = None,
    bold: bool = False,
    underline: bool = False,
    overwritable: bool = False
) -> None:
    """
    Prints a message to terminal with given color, bold and underline properties.
    """
    attrs = []
    if bold:
        attrs.append('bold')

    if underline:
        attrs.append("underline")

    cprint(
        message,
        color,
        highlight,
        attrs=attrs,
        end="\r" if overwritable else None)


def success(message: str):
    """
    Prints a green bold message to terminal.
    """
    out(message, color=SUCCESS_COLOR, bold=True)


def error(message: str):
    """
    Prints a red bold message to terminal.
    """
    out(message, color=ERROR_COLOR, bold=True)


def input(message: str, type=str, default=None):
    """
    Asks for input.
    """
    try:
        return click.prompt(
            "[{}] {}".format(
                colored(
                    "?",
                    color=ASK_COLOR),
                message),
            type=type,
            default=default)
    except click.Abort:
        raise KeyboardInterrupt


def choice(message: str, choices: list, default=None):
    """
    Asks for a choice.
    """
    return prompt(
        [List("choice", message=message, choices=choices, default=default)],
        raise_keyboard_interrupt=True).get("choice", default)


def confirm(message: str, default: bool = False) -> bool:
    """
    Asks for confirmation.
    """
    return prompt([Confirm('confirm', message=message, default=default)],
                  raise_keyboard_interrupt=True).get('confirm', default)


# class CLI:
#     _logger = logging.getLogger("CLI")

#     _BASE_BUILD_IMAGE_NAME = "fp_{}_build_image_{}-{}"
#     _DOCKER_FUNCTIONS_DIR = "/function"

#     @classmethod
#     def _build_image_name(cls, provider, runtime, version):
#         return cls._BASE_BUILD_IMAGE_NAME.format(provider, runtime, version)

#     def __init__(self) -> None:
#         self._image_manager = ImageManager(
#             build_image_file=join(CONFIG_DIR, "build_images.yml"))

#     def init(self, rebuild=False) -> None:
#         self._logger.info("Building base build images for all runtimes.")
#         self._image_manager.rebuild_all_images(force_rebuild=rebuild)

#     def profile(self, function_name: str, service: str, invocations: int = 1, redeploy: bool = False):
#         func_info = self.function_info(function_name)
#         if not func_info:
#             self._logger.error(f"No function found with name: {function_name}")

#         if not self.is_deployed(function_name):
#             self._logger.warn(f"Function {function_name} is not deploy. Deploying now:")
#             self.deploy_function(function_name)
#         elif redeploy:
#              self._logger.info(f"Redeploying function {function_name}")
#              self.deploy_function(function_name)

#         self._logger.info(f"Invoking function {function_name}")
#         output = run_command(f"sls invoke --function {function_name}")

#         self._logger.info(f"Function returned: {output}")


#     def new_function(self, name, runtime):
#         """
#         Generates a new function by calling a FunctionGenerator
#         """
#         FunctionGenerator.generate(name, runtime, self._image_manager, [])

#     def function_info(self, function_name: str) -> dict:
#         sls_config = serverless_config()

#         return sls_config.get("functions", {}).get(function_name)

#     def deploy_function(self, function_name: str):
#         self._logger.info(f"Deploying function {function_name}")
#         run_command(f"sls deploy --function {function_name}")
#         self._logger.info(f"Function {function_name} deployed")

#     def is_deployed(self, function_name: str) -> bool:
#         deployed_funcs = run_command("sls deploy list functions")

# return function_name in deployed_funcs and
# self.function_info(function_name) is not None
