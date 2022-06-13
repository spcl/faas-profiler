#
#   Dockerfile to build container for example functions
#

ARG FUNCTION_DIR="/function"
ARG RUNTIME_VERSION="3.8"
ARG DISTRO_VERSION="3.12"

# 1. STAGE: Base Image plus GCC
FROM python:${RUNTIME_VERSION}-alpine${DISTRO_VERSION} AS python-alpine

RUN apk add --no-cache \
    libstdc++

# 2. STAGE: Install Packages and Python requirements
FROM python-alpine AS build-image

RUN apk add --no-cache \
    build-base \
    libtool \
    autoconf \
    automake \
    libexecinfo-dev \
    make \
    cmake \
    libcurl \
    linux-headers \
    gcc

ARG FUNCTION_DIR
ARG RUNTIME_VERSION

RUN mkdir -p ${FUNCTION_DIR}
WORKDIR ${FUNCTION_DIR}

# Update pip
RUN python${RUNTIME_VERSION} -m pip install --upgrade pip

# Install faas-profiler
ADD dist wheels/
RUN python${RUNTIME_VERSION} -m pip install --find-links=wheels/ faas_profiler

# Cop example functions and install dependencies
ADD examples .
RUN python${RUNTIME_VERSION} -m pip install -r requirements_function.txt

# INSTALL AWS LAMBDA
RUN python${RUNTIME_VERSION} -m pip install awslambdaric

# 3. STAGE: Build final runtime
FROM python-alpine

ARG FUNCTION_DIR

WORKDIR ${FUNCTION_DIR}

COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
COPY examples/entry.sh /
RUN chmod 755 /usr/bin/aws-lambda-rie /entry.sh
ENTRYPOINT [ "/entry.sh" ]