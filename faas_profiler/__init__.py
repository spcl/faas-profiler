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
from os.path import join, exists
from glob import glob

from faas_profiler.config import EXAMPLES_DIR, Runtime, Provider
from faas_profiler.templating import (
    HandlerTemplate,
    GitIgnoreTemplate,
    AWSServerlessTemplate,
    GCPServerlessTemplate,
    AzureServerlessTemplate,
    RequirementsTemplate,
    TemplatingError
)


class CommandError(RuntimeError):
    pass


class Commands:
    """
    Welcome to the local FaaS Profiler SDK to test serverless functions with the profiler.
    """

    def new_application(self, application: str, runtime: str):
        """
        Generates a new application.
        """
        try:
            runtime = Runtime[runtime.upper()]
        except KeyError:
            cli.error(f"No runtime found with name: {runtime}."
                      f"Available are: {list(Runtime)}")
        else:
            try:
                Application.generate(application, runtime)
            except ValueError as err:
                cli.error(err)
                return

            cli.success(f"Application {application} created!")

    def new_function(
            self,
            application: str,
            function: str,
            provider: str = None):
        """
        Generates a new function

        If provider is None, the function will be created for all providers
        """
        try:
            provider = Provider[provider.upper()] if provider else None
        except KeyError:
            cli.error(f"No provider found with name: {provider}."
                      f"Available are: {list(Provider)}")
        else:
            try:
                app = Application.find_by(application)
            except ValueError as err:
                cli.error(err)
            else:
                app.generate_function(function, provider)

    def deploy(
        self,
        application: str,
        provider: Provider,
        function: str = None
    ) -> None:
        """
        Deploys the application.

        If function is None, the entire application gets deployed
        """
        try:
            provider = Provider[provider.upper()] if provider else None
        except KeyError:
            cli.error(f"No provider found with name: {provider}."
                      f"Available are: {list(Provider)}")
        else:
            app = Application.find_by(application)
            if app is None:
                cli.error(f"No application found with name {application}")
                return

            app.deploy(provider, function)
            cli.success("Application deployed")

    def invoke(
        self,
        application: str,
        provider: Provider,
        function: str,
        times: int = 1
    ) -> None:
        """
        Invokes the function inside the given application
        """
        try:
            provider = Provider[provider.upper()] if provider else None
        except KeyError:
            cli.error(f"No provider found with name: {provider}."
                      f"Available are: {list(Provider)}")
        else:
            app = Application.find_by(application)
            if app is None:
                cli.error(f"No application found with name {application}")
                return

            cli.out(f"Invoking {times} times function:")
            for i in range(0, times):
                cli.out(f"Invocation {i+1}/{times}")
                app.invoke(provider, function)

    def remove(self, application: str) -> None:
        """
        Removes the given application
        """
        app = Application.find_by(application)
        if app is None:
            cli.error(f"No application found with name {application}")
            return

        app.remove()


class Application:
    """
    Represents one example applications.
    """

    ACCEPTED_SLS_CONFIG = 'sls_*.yml'

    @staticmethod
    def find_all_applications() -> List[str]:
        """
        Returns a list of paths to example application within in the examples folder.
        Includes the path if a serverless config file is present.
        """
        subfolders = [f.path for f in os.scandir(EXAMPLES_DIR) if f.is_dir()]

        valid_applications = filter(
            lambda p: any(glob(join(p, Application.ACCEPTED_SLS_CONFIG))),
            subfolders)

        return list(valid_applications)

    @classmethod
    def find_by(cls, application_name: str) -> Type[Application]:
        path = join(EXAMPLES_DIR, application_name)
        if path not in Application.find_all_applications():
            raise ValueError(
                f"No application with name {application_name} found.")

        return cls(application_name, path)

    @classmethod
    def generate(
        cls,
        application_name: str,
        runtime: Runtime,
        aws_region: str = "eu-central-1",
        gcp_region: str = "europe-west3-a",
        azure_region: str = ""
    ) -> Type[Application]:
        """
        Generates a new example application inside 'examples'
        """
        cli.out(f"Generating new application {application_name}")
        path = join(EXAMPLES_DIR, application_name)
        if path in Application.find_all_applications():
            raise ValueError(
                f"Application with name {application_name} already exists")

        os.mkdir(path)
        cli.out(f"Created: {path}")

        gitignore_file = GitIgnoreTemplate.render(path)
        cli.out(f"Created: {gitignore_file}")

        aws_sls_file = AWSServerlessTemplate.render(path, context={
            "application_name": application_name,
            "runtime": runtime.value,
            "region": aws_region
        })
        cli.out(f"Created: {aws_sls_file}")

        gcp_sls_file = GCPServerlessTemplate.render(path, context={
            "application_name": application_name,
            "runtime": runtime.value,
            "region": gcp_region
        })
        cli.out(f"Created: {gcp_sls_file}")

        azure_sls_file = AzureServerlessTemplate.render(path, context={
            "application_name": application_name,
            "runtime": runtime.value,
            "region": azure_region
        })
        cli.out(f"Created: {azure_sls_file}")

        cls._generate_python_specific_files(path)

        return cls(application_name, path)

    @classmethod
    def _generate_python_specific_files(cls, path: str):
        gcp_sls_file = RequirementsTemplate.render(path)
        cli.out(f"Created: {gcp_sls_file}")

    def __init__(
        self,
        name: str,
        path: str
    ) -> None:
        self.name = name
        self.path = path

    def get_sls_config_path(self, provider: Provider) -> str:
        """
        Returns the serverless config file for given provider
        """
        path = join(self.path, f"sls_{provider.value}.yml")
        if not exists(path):
            return None

        return path

    def get_sls_config(self, provider: Provider) -> dict:
        """
        Returns the serverless config for given provider
        """
        path = self.get_sls_config_path(provider)
        if path is None:
            return {}

        with open(path, "r") as fp:
            return yaml.safe_load(fp)

    def get_functions(self, provider: Provider) -> dict:
        """
        Returns the functions of the application by provider
        """
        provider_config = self.get_sls_config(provider)
        return provider_config.get("functions", {})

    def flush_config(self, provider: Provider, config: dict) -> None:
        """
        Writes cached serverless config back to file
        """
        sls_path = self.get_sls_config_path(provider)
        if sls_path is None:
            return

        with open(sls_path, "w") as fp:
            yaml.dump(config, fp,
                      sort_keys=False,
                      default_flow_style=False)

    def get_runtime(self, provider: Provider) -> Runtime:
        """
        Returns the runtime of the application given the provider
        """
        runtime = self.get_sls_config(
            provider).get("provider", {}).get("runtime")

        try:
            return Runtime(runtime)
        except ValueError:
            return Runtime.UNKNOWN

    def deploy(
        self,
        provider: Provider,
        function_name: str = None
    ) -> None:
        """
        Deploys the application with serverless
        """
        sls_path = self.get_sls_config_path(provider)
        if sls_path is None:
            cli.error(f"No serverless config defined for {provider}")
            return

        command = f"sls deploy --config {sls_path}"
        if function_name and function_name in self.functions:
            command += f" --function {function_name}"

        cli.out(f"Deploying application with serverless...")
        cli.run_command(command, cwd=self.path)

    def invoke(self, provider: Provider, function_name: str) -> None:
        """
        Invokes the function
        """
        sls_path = self.get_sls_config_path(provider)
        if sls_path is None:
            cli.error(f"No serverless config defined for {provider}")
            return

        cli.out(f"Invoking function {function_name}...")
        output = cli.run_command(
            f"sls invoke --config {sls_path} --function {function_name}",
            cwd=self.path)

        cli.out(f"Function returned: {output}")

    def remove(self):
        """
        Removes the application
        """
        cli.out("Removing application with serverless...")
        cli.run_command("sls remove", cwd=self.path)

    def generate_function(
        self,
        function_name: str,
        provider: Provider = None,
        function_handler: str = "handler",
    ):
        """
        Generates a new function inside the application
        """
        cli.out(
            f"Generating function {function_name} for application {self.name}")

        cli.out("Creating handler file...")
        try:
            handler_file = HandlerTemplate.render(
                target_dir=self.path,
                file_name=function_name,
                context={"handler_name": function_handler})
        except TemplatingError as err:
            cli.error(err)
            return

        cli.out(f"Created: {handler_file}")

        for p in Provider:
            if provider is not None and p != provider:
                continue

            if function_name in self.get_functions(p):
                cli.error(
                    f"Function named {function_name} already exists in {self.name}")
                continue

            cli.out(f"Adding function to {p.value} serverless config...")
            self._add_function_to_serverless(
                p, function_name, function_handler)
            cli.out("Serverless config updated.")

    def _add_function_to_serverless(
        self,
        provider: Provider,
        function_name: str,
        function_handler: str,
    ) -> None:
        sls_config = self.get_sls_config(provider)
        sls_config.setdefault("functions", {})[function_name] = {
            "handler": f"{function_name}.{function_handler}"
        }

        self.flush_config(provider, sls_config)
