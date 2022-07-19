#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Templating-Engine
"""

import jinja2

import faas_profiler.cli as cli

from os.path import join, exists
from faas_profiler.config import TEMPLATES_DIR


class TemplatingError(RuntimeError):
    pass


class Template:
    template_file = None
    file_format = None
    file_name = None

    @classmethod
    def render(
        cls,
        target_dir: str,
        file_name: str = None,
        context={}
    ):
        """
        Renders and wirtes a new file based on a template.
        """
        if cls.template_file is None:
            raise TemplatingError(
                f"Template {cls.template_file} does not exists.")

        file_name = file_name if file_name else cls.file_name
        output_file = join(target_dir, file_name + cls.file_format)
        if exists(output_file):
            raise TemplatingError(
                f"File {file_name + cls.file_format} already exists in {target_dir}")

        template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATES_DIR)
        template_env = jinja2.Environment(
            loader=template_loader,
            autoescape=jinja2.select_autoescape([
                '.py-tpl', 'gitigonre.txt-tpl', 'serverless.yml-tpl']))

        try:
            template = template_env.get_template(cls.template_file)
        except jinja2.exceptions.TemplateNotFound:
            raise TemplatingError(
                f"Template {cls.template_file} does not exists.")
        else:
            with open(output_file, "w") as fp:
                fp.write(template.render(context))

            return output_file


class ProfilerConfigTemplate(Template):
    template_file = "faas_profiler.yml-tpl"
    file_format = ".yml"
    file_name = "faas_profiler"

    AVAILABLE_MEASUREMENTS = [
        "Common::WallTime",
        "Network::Connections",
        "Network::IOCounters",
        "Memory::Usage",
        "CPU::Usage",
        "Information::Environment",
        "Information::OperatingSystem",
        "Information::Payload",
    ]

    AVAILABLE_CAPTURES = [
        "AWS::S3Capture",
        "AWS::EFSCapture"
    ]

    AVAILABLE_EXPORTERS = [
        "Console",
        "Visualizer",
        "S3Uploader"
    ]

    @classmethod
    def render(
        cls,
        target_dir: str,
        file_name: str = None,
        context={}
    ):
        """
        Builds context for rendering and creates a customized profile config.
        """
        config_context = {}

        if cli.confirm("Do you want to perform measurements?", default=True):
            config_context['enable_measurements'] = True
            selected_measurements = cli.choice(
                "Select measurements to perform:",
                cls.AVAILABLE_MEASUREMENTS,
                multiple=True)
            config_context["active_measurements"] = {
                meas: meas in selected_measurements for meas in cls.AVAILABLE_MEASUREMENTS}
        else:
            config_context['enable_measurements'] = False
            config_context["active_measurements"] = {
                meas: False for meas in cls.AVAILABLE_MEASUREMENTS}

        if cli.confirm("Do you want to perform capturings?", default=True):
            config_context['enable_captures'] = True
            selected_captures = cli.choice(
                "Select captures to perform:",
                cls.AVAILABLE_CAPTURES,
                multiple=True)
            config_context["active_captures"] = {
                capt: capt in selected_captures for capt in cls.AVAILABLE_CAPTURES}
        else:
            config_context['enable_captures'] = False
            config_context["active_captures"] = {
                capt: False for capt in cls.AVAILABLE_CAPTURES}

        if cli.confirm(
            "Do you want to enable distributed tracing?",
                default=True):
            config_context['enable_tracing'] = True
        else:
            config_context['enable_tracing'] = False

        selected_exporters = cli.choice(
            "Select exporters to export the data:",
            cls.AVAILABLE_EXPORTERS,
            multiple=True)
        config_context["active_exporters"] = {
            expo: expo in selected_exporters for expo in cls.AVAILABLE_EXPORTERS}

        config_context["exporters_params"] = {}
        if config_context["active_exporters"]["S3Uploader"]:
            config_context["exporters_params"]["S3Uploader"] = cls._add_s3_exporter_parameters(
            )

        if config_context["active_exporters"]["Visualizer"]:
            config_context["exporters_params"]["Visualizer"] = cls._add_visualizer_parameters(
            )

        return super().render(
            target_dir, file_name, {
                **config_context, **context})

    @classmethod
    def _add_s3_exporter_parameters(cls) -> dict:
        return {
            "bucket": cli.input(
                "S3 Bucket to upload",
                str,
                "faas-profiler-results"),
            "folder": cli.input(
                "Folder",
                str,
                "")}

    @classmethod
    def _add_visualizer_parameters(cls) -> dict:
        return {
            "endpoint_url": cli.input("Visualizer Endpoint URL", str)
        }


class HandlerTemplate(Template):
    template_file = "handler.py-tpl"
    file_format = ".py"
    file_name = "handler"


class GitIgnoreTemplate(Template):
    template_file = "gitignore.txt-tpl"
    file_format = ""
    file_name = ".gitignore"


class AWSServerlessTemplate(Template):
    template_file = "serverless_aws.yml-tpl"
    file_format = ".yml"
    file_name = "sls_aws"


class GCPServerlessTemplate(Template):
    template_file = "serverless_gcp.yml-tpl"
    file_format = ".yml"
    file_name = "sls_gcp"


class AzureServerlessTemplate(Template):
    template_file = "serverless_azure.yml-tpl"
    file_format = ".yml"
    file_name = "sls_azure"


class RequirementsTemplate(Template):
    template_file = "requirements.txt-tpl"
    file_format = ".txt"
    file_name = "requirements"
