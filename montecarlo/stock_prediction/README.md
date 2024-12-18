# Stock Prediction with Monte Carlo Method

In this application, a Monte Carlo simulation is performed with Lithops over Cloud Functions to perform a stock prediction operation. It is a demonstration of how lithops can be used for these kind of computations.

## How is Monte Carlo Algorithm Used?


This notebook contains an example of stock prediction with Monte Carlo. The goal of this notebook is to demonstrate how IBM Cloud Functions can benefit Monte Carlo simulations and not how stock prediction works. As stock prediction is very complicated and requires many prior knowledge and correct models, we did not innovate the Monte Carlo Method for handling the unpredictability of stock prices, nor do we provide any results for prediction based on long term data sources.

## Running the code
- You need an IBM Cloud account and IBM Cloud Functions with IBM Cloud Object Storage.
- An Object storage bucket is needed to run this example.
- You have to be sure that lithops is installed and works fine.
### Installing the dependencies
```python
import numpy as np
import sys
from time import time
import matplotlib.pyplot as plt
import scipy.stats as scpy
import logging

#Install Lithops
try:
    import lithops
except:
    !{sys.executable} -m pip install lithops
    import lithops
```
### Implementation of Monte Carlo simulation

'StockData' is a Python class that we use to represent a single stock. You may configure the following parameters:

**MAP_INSTANCES:** 
number of IBM Cloud Function invocations. Default is 1000

**forecasts_per_map:**
forecasts_per_map - number of forecasts to run in a single invocation. Default is 100

**day2predict:**
number of days to predict for each forecast. Default is 730 days

Our code contains two major Python methods:

**process_forecasts(data=None):**
a function to process number of forecasts and
  days as configured. (aka "map" in map-reduce paradigm) 

**process_in_circle_points(self, results, futures):**
summarize results of all process_forecasts executions (aka "reduce" in map-reduce paradigm)

### Lithops Configuration

Configure access details to your IBM COS and IBM Cloud Functions. 'storage_bucket' should point to some pre-existing COS bucket. This bucket will be used by Lithops to store intermediate results. All results will be stored in the folder lithops.jobs. For additional configuration parameters see configuration section [here](https://github.com/lithops-cloud/lithops/tree/master/config/).

*An example of a config object:*
```python
config = {'lithops': {'backend': 'ibm_cf', 'storage': 'ibm_cos'},
          'ibm': {'iam_api_key': '<IAM_API_KEY>'},# If your namespace is IAM based (To reach cloud functions API without cf api key)
          'ibm_cf':  {'endpoint': '<CLOUD_FUNCTIONS_ENDPOINT>',
                      'namespace': '<NAME_OF_YOUR_NAMESPACE>',
                      'namespace_id': '<GUID_OF_YOUR_NAMESPACE>'# If your namespace is IAM based
                      #'api_key': 'YOUR_API_KEY' #If your namespace is foundary based
                     },
          'ibm_cos': {'storage_bucket': '<YOUR_COS_BUCKET_NAME>',
                      'region': '<BUCKET_REGION>',
                      'api_key': '<YOUR_API_KEY>'}}
```               
### Input data on the past stock prices
This step is mandatory to run our example. The raw stock daily data need to be prepared prior used by the code. You can follow the next steps to create different input data. You may use any spreadsheet for this process or any other tool.
- Fetch historical daily value of the stock from some reliable finance website
- Calculate ln() function of two consecutive days ln (today price / yesterday price )
- Calculate the variance 'var', the average 'u' and standard deviation of the previous results
- Calculate the drift by equation drift = u - (var^2 / 2 )

### Execution of simulation and conclusion
After getting the config and everything ready, a FunctionExecutor is created with the config provided in code. Here lithops' map_reduce function is called with *process_forecasts* as map function and *combine_forecasts* as the reduce function.
Then numbers of functions are performed parallelly.  Then with the result a graph is being drawen showing predicted prices and number of forecasts to predict them. Here we took advantage of cloud functions with lithops to use outer sources for performing a vast amount of random computation and in a scenerio where we paid for the machine or sources, we would have been paying just for the time spent for computation itself. 
