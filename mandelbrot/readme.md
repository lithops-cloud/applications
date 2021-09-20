# Cloudbutton Mandelbrot Set Calculation Example
## Serverless Matrix Multiplication
In this notebook the Mandelbrot set calculated on a limited space several times using the Cloudbutton toolkit. A certain region of the linear space is treated as a matrix and divided into chunks in order to be able to  be distributed among many functions. For each step, the corresponding image generated from the matrix will be plotted. The matrix is sliced into many chunks (as many as concurrency) so that each function will treat one of these. Thus, function arguments will be the limits or boundaries of a chunk.

## How to Run
You need an IBM Cloud account and IBM Cloud Functions with IBM Cloud Object Storage. You need to create an Object Storage bucket to run this application. You have to be sure that lithops is installed and works fine and your lithops configuration is done right. You can check out [https://github.com/lithops-cloud/lithops/tree/master/config](https://github.com/lithops-cloud/lithops/tree/master/config) for more information about configuration. Also dependencies listed below need to be installed prior to execution:
```python
import numpy as np
from math import sqrt
from matplotlib import colors
from matplotlib import pyplot as plt
from lithops.multiprocessing import Pool
```

## Execution
In this application, the distributed calculation of the Mandelbrot set is run starting from a certain point from space. Then, the boundaries are adjusted to perform a zoom in.  Firstly, parameters such as width, maxiter, concurrency, xtarget and ytarget were determined. Concurrency represents the number of functions to be executed in parallel. The corresponding image generated from the matrix using the determined parameters is going to be plotted for each step.
