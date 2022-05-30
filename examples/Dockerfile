#
#   Dockerfile to build container for examples
#
#   Usage (executed from project root):
#   docker build -t IMAGE_NAME -f examples/Dockerfile .  --build-arg function_name=FUNCTION_NAME

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

ARG function_name
ARG FUNCTION_DIR
ARG RUNTIME_VERSION

RUN mkdir -p ${FUNCTION_DIR}

# INSTALL PROFILER by copying files
ADD /faas_profiler ${FUNCTION_DIR}/faas_profiler
ADD requirements.txt ${FUNCTION_DIR}

WORKDIR ${FUNCTION_DIR}

RUN python${RUNTIME_VERSION} -m pip install -r requirements.txt --target ${FUNCTION_DIR}

# INSTALL FUNCTION by copying files
ADD examples/${function_name}/function.py ${FUNCTION_DIR}
ADD examples/${function_name}/requirements.function.txt ${FUNCTION_DIR}

RUN python${RUNTIME_VERSION} -m pip install -r requirements.function.txt --target ${FUNCTION_DIR}

# INSTALL AWS LAMBDA
RUN python${RUNTIME_VERSION} -m pip install awslambdaric --target ${FUNCTION_DIR}

# 3. STAGE: Build final runtime
FROM python-alpine

ARG FUNCTION_DIR

WORKDIR ${FUNCTION_DIR}

COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
COPY examples/entry.sh /
RUN chmod 755 /usr/bin/aws-lambda-rie /entry.sh
ENTRYPOINT [ "/entry.sh" ]
CMD [ "function.handler" ]