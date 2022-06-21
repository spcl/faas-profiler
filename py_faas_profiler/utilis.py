#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Dict
from inflection import underscore


class Registerable:

    _names_: Dict[str, Registerable] = {}

    name: str = ""
    name_parts: tuple = tuple()
    key: str = ""

    @classmethod
    def register(cls, name, module_delimiter: str = "::"):
        def decorator(subclass):
            cls._names_[name] = subclass
            subclass.name = name
            subclass.name_parts = tuple(underscore(part)
                                        for part in name.split(module_delimiter))
            subclass.key = "_".join(subclass.name_parts)

            return subclass
        return decorator

    @classmethod
    def factory(cls, name):
        try:
            return cls._names_[name]
        except KeyError:
            raise ValueError(
                f"Unknown measurement name {name}. Available measurements: {list(cls._measurements_.keys())}")
