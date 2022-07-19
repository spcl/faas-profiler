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
from inquirer import List, Checkbox, Confirm, prompt


def run_command(command, env=None, cwd=None):
    """
    Runs a given command in a subprocess.
    """
    command = split(command)

    process = Popen(
        command,
        stderr=PIPE,
        stdout=PIPE,
        env=env,
        cwd=cwd,
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


def choice(message: str, choices: list, multiple: bool = False, default=None):
    """
    Asks for a choice.
    """
    if multiple:
        return prompt(
            [Checkbox("choice", message=message, choices=choices, default=default)],
            raise_keyboard_interrupt=True).get("choice", default)

    return prompt(
        [List("choice", message=message, choices=choices, default=default)],
        raise_keyboard_interrupt=True).get("choice", default)


def confirm(message: str, default: bool = False) -> bool:
    """
    Asks for confirmation.
    """
    return prompt([Confirm('confirm', message=message, default=default)],
                  raise_keyboard_interrupt=True).get('confirm', default)
