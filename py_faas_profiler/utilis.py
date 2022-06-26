#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Dict
from inflection import underscore


def get_arg_by_key_or_pos(args, kwargs, pos, kw):
    try:
        return kwargs[kw]
    except KeyError:
        try:
            return args[pos]
        except IndexError:
            return None


def registerable_name_parts(name, delimiter: str = "::") -> tuple:
    return tuple(underscore(part) for part in name.split(delimiter))


def registerable_key(name, delimiter: str = "::", ) -> str:
    return "_".join(registerable_name_parts(name, delimiter))


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
            subclass.name_parts = registerable_name_parts(
                name, module_delimiter)
            subclass.key = registerable_key(name, module_delimiter)

            return subclass
        return decorator

    @classmethod
    def factory(cls, name):
        try:
            return cls._names_[name]
        except KeyError:
            raise ValueError(
                f"Unknown measurement name {name}. Available measurements: {list(cls._names_.keys())}")
