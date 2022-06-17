#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module to generate a new serverless function to profile.
"""
from __future__ import annotations

import logging
from typing import Type
import yaml
from abc import ABC, abstractmethod
from contextlib import contextmanager
from os.path import dirname, join, exists, basename
from os import makedirs
from shutil import copyfile

from faas_profiler.images import ImageManager

PROJECT_ROOT = dirname(dirname(__file__))
TEMPLATES_ABS = join(PROJECT_ROOT, "templates")
FUNCTIONS_ABS = join(PROJECT_ROOT, "functions")
FUNCTIONS_REL = "functions"


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


class FunctionGenerator(ABC):

    _logger = logging.getLogger("Function Generator")

    @classmethod
    def generate(
        cls,
        name,
        runtime: str,
        image_manager: Type[ImageManager],
        providers: list = [],
    ) -> Type[FunctionGenerator]:
        """
        Factory method to generate a new method based on runtime.
        """
        if runtime == "python":
            return PythonFunctionGenerator(
                name, runtime, providers, image_manager)
        elif runtime == "node":
            return NodeFunctionGenerator(
                name, runtime, providers, image_manager)
        else:
            cls._logger.error(f"No generator found for runtime {runtime}!")

    handler_command = "function.handler"
    entry_point = []

    def __init__(
        self,
        name: str,
        runtime: str,
        providers: list,
        image_manager: Type[ImageManager],
    ) -> None:
        self.name = name.replace(" ", "_").lower()
        self.func_abs_dir = join(FUNCTIONS_ABS, self.name)
        self.func_rel_dir = join(FUNCTIONS_REL, self.name)
        self.providers = providers
        self.runtime = runtime
        self.image_manager = image_manager

        # FIXME: Replace hardcoded aws
        self.build_image = image_manager.get_build_image("aws", runtime)

        self._create_method()

    @abstractmethod
    def copy_function_files(self) -> str:
        pass

    @abstractmethod
    def copy_dockerfile(self) -> str:
        pass

    def _create_method(self):
        self._logger.info(
            f"Generate a new function - name: {self.name}, runtime: {self.runtime}, providers: {self.providers}")
        if not exists(self.func_abs_dir):
            self._logger.info(f"CREATE: {self.func_abs_dir}")
            makedirs(self.func_abs_dir)
        else:
            self._logger.error(
                f"A function called '{self.name}' already exists. Abort.")

        function_entry_file = self.copy_function_files()
        dockerfile_path = self.copy_dockerfile()

        self._register_function(dockerfile_path)

        self._logger.info(
            f"Created function with entry file: {function_entry_file}")

    def _register_function(self, dockerfile_path: str):
        with update_serverless_config() as serverless_config:
            functions = serverless_config.setdefault('functions', {})
            images = serverless_config.setdefault(
                'provider',
                {}).setdefault(
                'ecr',
                {}).setdefault(
                'images',
                {})

            image_name = "{}_image".format(self.name)

            functions[self.name] = {
                "image": {
                    "command": self.handler_command,
                    "entryPoint": self.entry_point,
                    "name": image_name
                }
            }
            images[image_name] = {
                "path": self.func_rel_dir,
                "file": basename(dockerfile_path),
                "buildArgs": {
                    "BASE_IMAGE": self.build_image.tags[0],
                    "FUNCTION_DIR": self.image_manager.docker_functions_dir
                }
            }


class NodeFunctionGenerator(FunctionGenerator):

    handler_command = "function.handler"
    entry_point = ["/usr/local/bin/npx", "aws-lambda-ric"]

    def copy_function_files(self):
        """
        Copies the a node function template.
        """
        func_file = join(self.func_abs_dir, "function.js")
        self._logger.info(f"CREATE: {func_file}")
        copyfile(
            src=join(TEMPLATES_ABS, "aws_function_template.js"),
            dst=func_file)

        return func_file

    def copy_dockerfile(self):
        """
        Copies a dockerfile template.
        """
        dockerfile = join(self.func_abs_dir, "Dockerfile.aws")
        self._logger.info(f"CREATE: {dockerfile}")
        copyfile(
            src=join(TEMPLATES_ABS, "Dockerfile.node_template"),
            dst=dockerfile)

        return dockerfile


class PythonFunctionGenerator(FunctionGenerator):

    handler_command = "function.handler"
    entry_point = ["/usr/local/bin/python", "-m", "awslambdaric"]

    def copy_function_files(self) -> str:
        """
        Copies the a python function template.
        """
        func_file = join(self.func_abs_dir, "function.py")
        self._logger.info(f"CREATE: {func_file}")
        copyfile(
            src=join(TEMPLATES_ABS, "aws_function_template.py"),
            dst=func_file)

        return func_file

    def copy_dockerfile(self) -> str:
        """
        Copies a dockerfile template.
        """
        dockerfile = join(self.func_abs_dir, "Dockerfile.aws")
        self._logger.info(f"CREATE: {dockerfile}")
        copyfile(
            src=join(TEMPLATES_ABS, "Dockerfile.python_template"),
            dst=dockerfile)

        return dockerfile
