
# Hyperparameter tuning grid search example

In this notebook, hyperparameter tuning using grid search algorithm is demonstrated.We have a dataset consisting
of amazon product reviews and a sklearn classifier to classiy these reviews. We take advantage of cloud functions
to tune this classifier's hyperparameters and show how Lithops can be used for this kind of computations.

## Grid Search
In machine learning', **hyperparameter optimization** or tuning is the problem of choosing a set of optimal hyperparameters for a learning algorithm. A hyperparameter is a parameter whose value is used to control the learning process. By contrast, the values of other parameters (typically node weights) are learned.

The traditional way of performing hyperparameter optimization has been  _grid search_, or a  _parameter sweep_, which is simply an  exhaustive searching through a manually specified subset of the hyperparameter space of a learning algorithm. A grid search algorithm must be guided by some performance metric, typically measured by  cross-validation on the training set or evaluation on a held-out validation set.

Since the parameter space of a machine learner may include real-valued or unbounded value spaces for certain parameters, manually set bounds and discretization may be necessary before applying grid search.
## Installing Dependencies

```python
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline

import joblib

from pprint import pprint
from time import time
import click
import bz2
```

## Download dataset

Download the dataset from [here](https://www.kaggle.com/bittlingmayer/amazonreviews) and extract the zip folder
`load_data` function seperates the data as X and Y arrays to prepare them for classifier.

## Run

Firt of all, you need to build the runtime from this [Dockerfile](runtime/Dockerfile) using:

   ```bash
   $ lithops runtime build -f Dockerfile lithops-sklearn:01
   ```

Your Lithops config file should look something similar to (you should also increase the data limit in Cloud Function invocations):
```bash
lithops:
    storage: aws_s3
    backend: aws_lambda
    data_limit : 6

aws:
    access_key_id :  <YOUR_AWS_KEY_ID>
    secret_access_key : <YOUR_AWS_ACCESS_KEY>
    runtime : lithops-sklearn:01
    runtime_memory : 1024 

aws_s3:
    region_name : <AWS_REGION>
    storage_bucket: <S3_BUCKET>

aws_lambda:
    execution_role: <YOUR_AWS_ROLE>
    region_name: <AWS_REGION>

```

You can see options and run the code with the lines below. This application is not meant to be run on the noteebok. You may encounter problems if you try to run it on Jupyter Notebook.

   ```bash
   $ python3 gridsearch.py --help
   ```

   ```bash
   $ python3 gridsearch.py --backend lithops --mib 10
   
   ```
---

In this block you can edit options and change default values for arguments taken. To run it using Lithops you must use the `--backend lithops` option.

```python
@click.command()
@click.option('--backend', default='loky', help='Joblib backend to perform grid search '
                                                '(loky | lithops | dask | ray | tune)')
@click.option('--address', default=None, help='Scheduler address (dask) or head node address '
                                              '(ray, ray[tune])')
@click.option('--mib', default=10, type=int, help='Load X MiB from the dataset')
@click.option('--refit', default=False, is_flag=True, help='Fit the final model with the best '
                                                           'configuration and print score')
@click.option('--jobs', default=-1, help='Number of jobs to execute the search. -1 means all processors.')
```

In the main function, grid search is performed using GridSearchCV from sklearn library with different parameters depending on the backend chosen. 
