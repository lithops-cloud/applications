# Lithops Moments in Time dataset example
## Video/image prediction

In this notebook we will process video clips from the MiT dataset at scale with Lithops by predicting the actions with a pretrained ResNet50 model and then counting how many occurrences of each category have been predicted.

## Running the code
To run this example you should have the requirements listed below:

 -   You need an IBM Cloud account and IBM Cloud Functions with IBM Cloud Object Storage.
-   An Object storage bucket is needed to run this example.
-   You have to be sure that lithops is installed and works fine.
-  You need a Redis account and Lithops configured accordingly.
-  You need access to dockerhub to use the runtime used in the program. (Or you can build your own runtime following the instructions [here](https://github.com/lithops-cloud/lithops/tree/master/runtime/ibm_cf).)
### Installing the dependencies
You should install the listed dependencies to run the example:
```python
import time
import builtins
import torch.optim
import torch.nn.parallel
from torch import save, load
from torch.nn import functional as F

from utils import extract_frames
from models import load_model, load_transform, load_categories

from lithops.multiprocessing import Pool, Queue
from lithops.multiprocessing.util import get_uuid
```
### Backends

The same program can be run in a local environment with processes or executed by functions in the cloud. After we choose a backend, only a few file locations must be changed. In this example we will be using the cloud functions backend.

We will be using a custom runtime for our functions which has torch, torchvision, ffmpeg and opencv-python modules already installed. We will store the pretrained weights in the cloud so that functions can access it. Then, after functions get the models weights they will start preprocessing input videos and inferring them one by one.

Later in this example, a little improvement detail to this process will be discussed.

### Download pretrained ResNet50 model weights and save them in a directory accessible by all functions 
Files are downloaded during execution with the code block below. You can also download them manually from [here](http://moments.csail.mit.edu/moments_models/moments_RGB_resnet50_imagenetpretrained.pth.tar) and pass the execution of the block.
```python
ROOT_URL = 'http://moments.csail.mit.edu/moments_models'
WEIGHTS_FILE = 'moments_RGB_resnet50_imagenetpretrained.pth.tar'

if not os.access(WEIGHTS_FILE, os.R_OK):
    os.system('wget ' + '/'.join([ROOT_URL, WEIGHTS_FILE]))

with builtins.open(WEIGHTS_FILE, 'rb') as f_in:
    weights = f_in.read()
with open(weights_location, 'wb') as f_out:
    f_out.write(weights)
```
### Map functions

Similar to the  `multiprocessing`  module API, we use a Pool to map the video keys across n workers (concurrency). However, we do not have to instantiate a Pool of n workers  _specificly_, it is the map function that will invoke as many workers according to the length of the list.

## Performance improvement

Now, since we know every function will have to pull the model weights from the cloud storage, we can actually pack these weights with the runtime image and reduce the start-up cost substantially.

---
 - ### Dockerfiles and build scripts for both runtimes can be found in the runtime/ folder.

 - ### Source code adapted from the demonstration in  [https://github.com/zhoubolei/moments_models]

 - ### Moments in Time article:  [http://moments.csail.mit.edu/#paper](http://moments.csail.mit.edu/#paper)
