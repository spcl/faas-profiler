#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profile package
"""
from __future__ import annotations

import os
import yaml
import faas_profiler.cli as cli

from typing import List, Type
from cached_property import cached_property
from os.path import join, exists

from faas_profiler.config import EXAMPLES_DIR
from faas_profiler.templating import HandlerTemplate, GitIgnoreTemplate, ServerlessTemplate


class CommandError(RuntimeError):
    pass


class Commands:
    """
    Welcome to the local FaaS Profiler SDK to test serverless functions with the profiler.
    """

    def __init__(self) -> None:
        self.examples = ExamplesManager()
        self._config = {}


class ExamplesManager:
    """
    Manage and generate example serverless applications and functions.
    """

    def generate(self, application: str, function: str = None):
        """
        Generates a new function and application
        """
        if application and function is None:
            cli.out(f"Generating new application {application}")
            app = Application.generate(application)
            cli.success(f"Application {application} created!")
        elif application and function:
            try:
                app = Application.by_name(application)
            except ValueError as err:
                if not cli.confirm(
                    f"Application {application} does not exists. Do you want to create it?",
                        default=True):
                    return

                cli.out(f"Generating new application {application}")
                app = Application.generate(application)
                cli.success(f"Application {application} created!")

            cli.out(
                f"Generating function {function} for application {application}")
            app.generate_function(function)
            cli.success(f"Function {function} created!")


class Application:
    """
    Represents one example applications.
    """

    ACCEPTED_SLS_CONFIG = ['sls.yml', 'serverless.yml']

    @staticmethod
    def find_all_applications() -> List[str]:
        """
        Returns a list of paths to example application within in the examples folder.
        Includes the path if a serverless config file is present.
        """
        subfolders = [f.path for f in os.scandir(EXAMPLES_DIR) if f.is_dir()]
        valid_applications = filter(
            lambda p: any(exists(join(p, sls_file))
                          for sls_file in Application.ACCEPTED_SLS_CONFIG),
            subfolders)

        return list(valid_applications)

    @classmethod
    def by_name(cls, application_name: str) -> Type[Application]:
        path = join(EXAMPLES_DIR, application_name)
        if path not in Application.find_all_applications():
            raise ValueError(
                f"No example application found with name: {application_name}")

        return cls(application_name, path)

    @classmethod
    def generate(cls, application_name: str) -> Type[Application]:

        path = join(EXAMPLES_DIR, application_name)
        if path in Application.find_all_applications():
            raise ValueError(
                f"Application with name {application_name} already exists")

        os.mkdir(path)
        cli.out(f"Created: {path}")

        gitignore_file = GitIgnoreTemplate.render(path)
        cli.out(f"Created: {gitignore_file}")

        serverless_file = ServerlessTemplate.render(path, context={
            "application_name": application_name
        })
        cli.out(f"Created: {serverless_file}")

        return cls(application_name, path)

    def __init__(
        self,
        name: str,
        path: str
    ) -> None:
        self.name = name
        self.path = path

        self._sls_config = None

    @cached_property
    def sls_config_path(self) -> str:
        """
        Returns the path to the serverless config file.

        Raises Error, if file not found or more than one is found.
        """
        sls_files = filter(
            exists, [join(self.path, s) for s in self.ACCEPTED_SLS_CONFIG])
        sls_files = list(sls_files)

        if len(sls_files) == 0:
            raise RuntimeError(
                f"Could not find a serverless config file in {self.path}"
                "Please check the application.")

        if len(sls_files) > 1:
            raise RuntimeError(
                f"Found more than one serverless config file in {self.path}"
                "Please provide only one.")

        return sls_files[0]

    @cached_property
    def sls_config(self) -> dict:
        """
        Returns parsed the serverless config
        """
        with open(self.sls_config_path, "r") as fp:
            return yaml.safe_load(fp)

    def flush_config(self):
        """
        Writes cached serverless config back to file
        """
        with open(self.sls_config_path, "w") as fp:
            yaml.dump(self.sls_config, fp,
                      sort_keys=False,
                      default_flow_style=False)

        del self.__dict__['sls_config']

    @property
    def functions(self) -> dict:
        """
        Returns a dict of currently defined serverless functions
        """
        return self.sls_config.get("functions", {})

    def generate_function(
        self,
        function_name: str,
        function_handler: str = "handler"
    ):
        """
        Generates a new function inside the application
        """
        if function_name in self.functions:
            raise ValueError(
                f"Function named {function_name} already exists in {self.name}")

        cli.out("Creating handler file...")
        handler_file = HandlerTemplate.render(
            target_dir=self.path,
            file_name=function_name,
            context={"handler_name": function_handler})
        cli.out(f"Created: {handler_file}")

        cli.out("Adding function to serverless config...")
        self._add_function_to_serverless(function_name, function_handler)
        cli.out("Serverless config updated.")

    def _add_function_to_serverless(
        self,
        function_name: str,
        function_handler: str
    ) -> None:
        functions = self.sls_config.setdefault("functions", {})
        functions[function_name] = {
            "handler": f"{function_name}.{function_handler}"
        }

        self.flush_config()
