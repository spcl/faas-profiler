# FaaS-Profiler

# NOT UP TO DATE

**Prerequisites**
- Docker
- Node and Serverless framework [Install instructions](https://www.serverless.com/framework/docs/getting-started)
- Python

## Getting Started with Python
### Install FaaS-Profiler
Install FaaS Profiler with conda (or any other environment manager):

1. Create and activate new environment:
```
conda create -n FaaS-Profiler_env python=3.8
conda activate FaaS-Profiler_env
```
2. Install packages
```
pip install -r ./requirements.txt
pip install -r ./py_faas_profiler/requirements.txt
```
3. Install FaaS-Profiler
```
pip install -e <root dir of repo (where setup.py is located)>
```
### Build base images
To build all base images for, execute:
```
fp init
```
To rebuild the images later, e.g. after the `py_faas_profiler` or `js_faas_profiler` package has been edited, execute:
```
fp init --rebuild True
```

### Create new function
To automatically generate a new function to be profiled, execute:
```
fp new_function <NAME> <python/node>
```
This automatically creates a new folder in functions with the placeholder source code.
A Dockerfile was also created, this takes the runtime base image as an argument and is only to be changed for function-specific ones.

The `serverless.yml` was also adapted. Please check manually if the new function has the necessary rights for special resources.

### Deploy and profile a function
To adjust what is to be profiled, change the fp_config.yml in the respective folder.

Deploy and profile a function:
```
fp profile <NAME> <PROVIDER (aws)>
```

Add the flag `--redeploy True` to force a new deployment of the function (NOT the whole service).


## Results
If the exporter `DashboardUploader` has been activated, the results can be viewed here: https://faas-profiler.herokuapp.com