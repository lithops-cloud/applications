# GROMACS Computations

ROMACS is a versatile package to perform molecular dynamics, i.e. simulate the Newtonian equations of motion for systems with hundreds to millions of particles.

It is primarily designed for biochemical molecules like proteins, lipids and nucleic acids that have a lot of complicated bonded interactions, but since GROMACS is extremely fast at calculating the nonbonded interactions (that usually dominate simulations) many groups are also using it for research on non-biological systems, e.g. polymers. GROMACS supports all the usual algorithms you expect from a modern molecular dynamics implementation, but there are also quite a few features that make it stand out from the competition. Check out [http://www.gromacs.org](http://www.gromacs.org/) for more information.

In this example, there is only one function that we execute over cloud functions. This function downloads the benchMEM benchmark set and executes the shell command for running the gromacs software with the given parameters and uploads the results to IBM COS. It is a demonstrarion of how we can run gromacs over cloud functions without spendindg any local resource. 

## How to Run

### IBM Cloud

You need an IBM Cloud account and IBM Cloud Functions with IBM Cloud Object Storage. You need to create an Object Storage bucket to run this application. You have to be sure that lithops is installed and works fine and your lithops configuration is done right. You can check out [https://github.com/lithops-cloud/lithops/tree/master/config](https://github.com/lithops-cloud/lithops/tree/master/config) for more information about configuration. Also dependencies listed below need to be installed prior to execution:
```python
import lithops
import os
import zipfile
import time
import wget
import json
```
Currently, the runtime cactusone/lithops-gromacs:1.0.2 uses Python3.8, so you must run the application with Python3.8. You need access to dockerhub to use the runtime used in the program, or you can build your own runtime with another python version following the instructions [here](https://github.com/lithops-cloud/lithops/tree/master/runtime). If you created your own runtime don't forget to replace the line below with your `docker_username/runtimename:tag`.
```python
fexec  =  lithops.FunctionExecutor(runtime='cactusone/lithops-gromacs:1.0.2', runtime_memory=2048)
```
You can find the dockerfile required to create your own runtime [here](runtime/Dockerfile.py3.10). 

### AWS

We also provide a small [execution demo in AWS](./gromacs.ipynb). Input data is publicly available at [lithops-applications-data](https://lithops-applications-data.s3.us-east-1.amazonaws.com/), users should upload it to their custom bucket with [import_dataset_aws.sh](../import_datasets_aws.sh) (incurs into "Requester pays" billing).

To run the AWS example, simply run the [gromacs.ipynb](gromacs.ipynb) notebook following the AWS-specific steps. The default python version is 3.10, but you can change it by simply adapting the first line of the [Dockerfile](runtime/Dockerfile.py3.10).

