#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module to build base build images.
"""

import logging
import yaml
import docker
from os.path import exists


class ImageManager:

    _logger = logging.getLogger("Image Manager")

    docker_functions_dir = "/function"

    BASE_BUILD_IMAGE_NAME = "fp_{}_build_image_{}-{}"

    @classmethod
    def build_image_tag(cls, provider: str, runtime: str, version: str) -> str:
        return cls.BASE_BUILD_IMAGE_NAME.format(provider, runtime, version)

    def __init__(self, build_image_file: str) -> None:
        self._logger.info(f"Setting docker client from default socket.")
        self._docker = docker.from_env()
        self._build_images_config = self._parse_build_config(build_image_file)

    def build_image_exists(self, provider, runtime, version="*") -> bool:
        """
        Returns true if a build image for given provider, runtime and version exits locally.
        """
        return self.get_build_image(provider, runtime, version) is not None

    def get_build_image(self, provider, runtime, version="*"):
        """
        Returns a build image for given provider, runtime and version exits locally.
        """
        image_tag = self.build_image_tag(provider, runtime, version)
        images = self._docker.images.list(image_tag)
        if len(images) > 1:
            self._logger.error(
                f"Searching for {image_tag} returned more than one image.")
            return None

        if len(images) == 1:
            return images[0]

        return None

    def rebuild_all_images(self, force_rebuild: bool = False) -> None:
        """
        (Re-)build images according to the configuration.
        """
        for provider, runtimes in self._build_images_config.items():
            for runtime, config in runtimes.items():
                runtime_version = config.get("runtime_version")
                image_tag = self.build_image_tag(
                    provider, runtime, runtime_version)
                if force_rebuild:
                    self._logger.info(f"BUILDING (FORCED): {image_tag}")
                    self.build_image(provider, runtime, config)
                elif not self.build_image_exists(provider, runtime, runtime_version):
                    self._logger.info(f"BUILDING (MISSING): {image_tag}")
                    self.build_image(provider, runtime, config)
                else:
                    self._logger.info(
                        f"BUILD SKIPPING: {image_tag}. Already defined.")

    def build_image(self, provider: str, runtime: str, config: dict):
        """
        Builds a single build base image based on the configuration.
        """
        dockerfile = config.get("build_dockerfile")
        if dockerfile is None:
            self._logger.error(
                f"Cannot build image without dockerfile. Abort.")

        runtime_version = config.get("runtime_version")
        distro_version = config.get("distribution_version")

        self._docker.images.build(
            tag=self.build_image_tag(provider, runtime, runtime_version),
            path=".",
            dockerfile=dockerfile,
            buildargs={
                'RUNTIME_VERSION': str(runtime_version),
                'DISTRO_VERSION': str(distro_version),
                'FUNCTION_DIR': self.docker_functions_dir
            },
            quiet=False)

    def _parse_build_config(self, file: str) -> dict:
        """
        Parses config ymal file to dict.
        """
        self._logger.info(f"Parse configuration file: {file}")
        if not exists(file):
            return

        with open(file, "r") as fh:
            return yaml.safe_load(fh)
