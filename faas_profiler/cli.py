#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-profiler cli module.

Contains functionality for interacting with the profiler via command line.
"""

from subprocess import Popen, PIPE
from shlex import split
from time import sleep
from os.path import dirname, join, exists
from os import makedirs
from shutil import copyfile

import logging

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

class Generators:
    logger = logging.getLogger("Generators")

    FUNCTIONS_DIR = join(dirname(dirname(__file__)), "functions")
    TEMPLATES_DIR = join(dirname(dirname(__file__)), "templates")

    @classmethod
    def create_function(cls, name, runtime="python3.8") -> bool:
        cls.logger.info(f"Generate a new function. Name: {name}, runtime: {runtime}")
        if not exists(cls.FUNCTIONS_DIR):
            makedirs(cls.FUNCTIONS_DIR)

        function_dir = join(cls.FUNCTIONS_DIR, name)
        if exists(function_dir):
            cls.logger.error(f"A function called '{name}' already exists. Abort.")
            return False

        cls.logger.info(f"CREATE: {function_dir}")
        makedirs(function_dir)

        handler_file = join(function_dir, "function.py")
        cls.logger.info(f"CREATE: {handler_file}")
        copyfile(
            src=join(cls.TEMPLATES_DIR, "aws_function_template.py"),
            dst=handler_file)

        dockerfile_aws = join(function_dir, "Dockerfile.aws")
        cls.logger.info(f"CREATE: {dockerfile_aws}")
        copyfile(
            src=join(cls.TEMPLATES_DIR, "Dockerfile.template"),
            dst=dockerfile_aws)


        dockerfile_gcp = join(function_dir, "Dockerfile.gcp")
        cls.logger.info(f"CREATE: {dockerfile_gcp}")
        copyfile(
            src=join(cls.TEMPLATES_DIR, "Dockerfile.template"),
            dst=dockerfile_gcp)


        dockerfile_azure = join(function_dir, "Dockerfile.azure")
        cls.logger.info(f"CREATE: {dockerfile_azure}")
        copyfile(
            src=join(cls.TEMPLATES_DIR, "Dockerfile.template"),
            dst=dockerfile_azure)

        return True


class CLI:
    logger = logging.getLogger("CLI")


    GENERATORS = {
        "function": Generators.create_function
    }

    @classmethod
    def generate(cls, generator: str, *args, **kwargs):
        if generator not in cls.GENERATORS.keys():
            cls.logger.error(f"No generator found for {generator}. Available: {list(cls.GENERATORS.keys())}")
            return
        
        if cls.GENERATORS[generator](*args, **kwargs):
            cls.logger.info("Generation successful.")

