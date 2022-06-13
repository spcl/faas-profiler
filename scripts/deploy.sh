#!/bin/sh

# Shell script to build faas_profiler package and deploy it with serverless

source scripts/_common.sh

# Read out funtion name
# if [ -z $1 ]; then
#     error "Please provide a function name."
#     exit 1
# fi

bot "Deploy a new serverless function"

# Make sure docker cli is installed and running
running "Check if docker is running..."
if ! [ -x "$(command -v docker)" ]; then
    error "Docker client is not running. Please make sure docker is up."
    exit 1
else
    ok "Docker is running."
fi

# Make sure that serverless is installed
running "Check if serverless package is installed..."
if ! [ -x "$(command -v serverless)" ]; then
    running "Serverless is not installed. Installing serverless..."
    
    npm install -g serverless;
    ok "Serverless installed."
else
    ok "Serverless is installed. Skipping."
fi

# Build faas profiler package
running "Check if build tools are installed..."
python3 -m pip install --upgrade pip
if ! pip3 list | grep wheel &> /dev/null; then
    running "Installing build tools..."
    pip3 install wheel;
    ok "Build tools installed."
else
    ok "Build tools already installed."
fi

running "Building faas profiler wheel..."
python3 setup.py bdist_wheel 

ok "Created wheel for faas profiler."

# Running serverless deploy
running "Deploy example function with serverless..."
sls deploy
ok "Deployed."
