# AirBnB sentiment analysis of the comments from multiple cities

Login to the [IBM Watson Studio](https://dataplatform.cloud.ibm.com/), first you need to activate watson services on your account to access the download links below. After downloading the Airbnb dataset, upload it to a COS bucket. The dataset consists of information -like review, reviewer info, coordinates- of the reviews from Airbnb.

1. [Amsterdam](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ec829133)
2. [Antwerp Belgium](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592c89d137)
3. [Athens Europe](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ec8398a0)
4. [Austin](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592c8b8a6d)
5. [Barcelona](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ec879780)
6. [Berlin](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ec8ae188)
7. [Boston](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ec8c2a9e)
8. [Brussels](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ec8d08f9)
9. [Chicago](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ec8e2af2)
10. [Dublin](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592c9752a0)
11. [London](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ec9811af)
12. [Los Angeles](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592ca6facb)
13. [Madrid](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592caa49fa)
14. [Palma Mallorca Spain](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8eca6879c)
15. [Melbourne](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592cb0353e)
16. [Montreal](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/907ad5190de7a698ecd285f10ea8af3e)
17. [Nashville](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592cb481b9)
18. [New Orleans](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592cb67b55)
19. [New York City](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ecbaf803)
20. [Oakland](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ecbb647e)
21. [Paris](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/12ec25711104b11d00482a0eb12bf2aa)
22. [Portland](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/12ec25711104b11d00482a0eb130c106)
23. [San Diego](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ecdc8216)
24. [City of San Francisco](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ece0160c)
25. [Santa Cruz](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ece029e3)
26. [Seattle](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ece36259)
27. [Sydney](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/907ad5190de7a698ecd285f10ee84fe2)
28. [Toronto](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592cf201d7)
29. [Trento](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/9fc8543fabfc26f908cf0c592cf27867)
30. [Vancouver](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/107ab470f90be9a4815791d8ecf62bba)
31. [Venice Italy](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/907ad5190de7a698ecd285f10efc4f45)
32. [Vienna Austria.](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/f2f07c6b6d8bb541a5785c6f1c06fdd2)
33. [Washington D.C.](https://dataplatform.cloud.ibm.com/api/exchange/actions/download-dataset/c3af8034bd7f7374f87b3df64209f055)


## How to run the application

First, you need to install required packages. 

```python
import io
import base64
import time
import shutil
import csv
import lithops
import regex
import re
import matplotlib.pyplot as plt
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
```
 Then you should set the BUCKET variable as the name of the bucket which you uploaded the dataset.
 
```python
 BUCKET = ['<YOUR_BUCKET_NAME>']
```
There are 2 major functions in this example:

- **analyze_comments:** It is used as the map function in map reduce paradigm. The function parses the dataset and classifies the reviews using nltk by their polarity scores and groups them by being positive, negative or neutral. 

- **create_map:** This method functions as the reduce function in this scenario. It reduces all the intermediate data grouped by sentiments and draws a map displaying the results in different colors accordingly.

## Configuration

### IBM Cloud

This is the original code of the experiments presented in [Serverless Data Analytics in the IBM Cloud](https://dl.acm.org/doi/abs/10.1145/3284028.3284029). You need to configure lithops with your own IBM account keys. You can also see more options about the configuration [here](https://github.com/lithops-cloud/lithops/tree/master/config).
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

## AWS

We also provide a small [execution demo in AWS](./map_sentiment_analysis.ipynb). Input data is publicly available at [lithops-applications-data](https://lithops-applications-data.s3.us-east-1.amazonaws.com/), users should upload it to their custom bucket with [import_dataset_aws.sh](../import_datasets_aws.sh) (incurs into "Requester pays" billing).

To run the AWS example, simply run the [map_sentiment_analysis.ipynb](map_sentiment_analysis.ipynb) notebook following the AWS-specific steps.

