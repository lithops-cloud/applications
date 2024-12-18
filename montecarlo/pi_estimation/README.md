# Pi Estimation with Monte Carlo Method

In this application, a Monte Carlo simulation is performed with Lithops over Cloud Functions to estimate the value of the number pi. It is a demonstration of how lithops can be used for these kind of computations.

## How is Monte Carlo Algorithm Used?

![pi](https://upload.wikimedia.org/wikipedia/commons/8/84/Pi_30K.gif)


In this example, the alue of the number pi is being estimated using Monte Carlo method. Monte Carlo methods are a broad class of computational algorithms that rely on repeated random sampling to obtain numerical results. For estimation of pi it works like this:
- 1. Fit a quadrant inside a square area.
- 2. Generate random points/ numbers along this area.
- 3. Calculate the numbers of the points that are in the quadrant
- 4. Calculate the ratio of number of points inside the quadrant to total number of points.
- 5. Multiply the ratio by 4 and this result is the estimation of pi.

## Running the code
- You need an IBM Cloud account and IBM Cloud Functions with IBM Cloud Object Storage.
- An Object storage bucket is needed to run this example.
- You have to be sure that lithops is installed and works fine.

### Implementation of Monte Carlo simulation

'EstimatePI' is a Python class that we use to represent a single PI estimation. You may configure the following parameters:

**MAP_INSTANCES:** 
number of IBM Cloud Function invocations. Default is 100  

**randomize_per_map:**
number of points to random in a single invocation. Default is 10,000,000

Our code contains two major Python methods:

**randomize_points(self,data=None)**
a function to random number of points and return the percentage of points that inside the circle  

**process_in_circle_points(self, results, futures):**
 summarize results of all randomize_points executions (aka "reduce" in map-reduce paradigm)
All your files and folders are presented as a tree in the file explorer. You can switch from one to another by clicking a file in the tree.

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
### Execution of simulation and conclusion

After getting the config and everything ready, a FunctionExecutor is created with the config provided in code. Here lithops' map_reduce function is called with *randomize_points* as map function and *process_in_circle_points* as the reduce function.
Then 1,000,000,000 points are generated and calculated if it is in the circular area parallelly.  Here we took advantage of cloud functions with lithops to use outer sources for performing a vast amount of random computation and in a scenerio where we paid for the machine or sources, we would have been paying just for the time spent for computation itself. As it is shown below it is 211 seconds for 100 IBM Cloud Functions with 1,000,000,000 random generations and calculations.