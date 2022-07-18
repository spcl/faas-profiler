#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Templating-Engine
"""

import jinja2

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
        # if exists(output_file):
        #     raise TemplatingError(
        # f"File {file_name + cls.file_format} already exists in {target_dir}")

        template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATES_DIR)
        template_env = jinja2.Environment(
            loader=template_loader,
            autoescape=jinja2.select_autoescape(['.py-tpl']))

        try:
            template = template_env.get_template(cls.template_file)
        except jinja2.exceptions.TemplateNotFound:
            raise TemplatingError(
                f"Template {cls.template_file} does not exists.")
        else:
            with open(output_file, "w") as fp:
                fp.write(template.render(context))

            return output_file


class HandlerTemplate(Template):
    template_file = "handler.py-tpl"
    file_format = ".py"
    file_name = "handler"
