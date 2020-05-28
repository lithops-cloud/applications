```python
import os
import io
import time

from torch import save, load
import torch.optim
import torch.nn.parallel
from torch.nn import functional as F

import models
from utils import extract_frames, load_frames, render_frames

from cloudbutton import Pool, CloudStorage

ROOT_URL = 'http://moments.csail.mit.edu/moments_models'
WEIGHT_FILE = 'moments_RGB_resnet50_imagenetpretrained.pth.tar'
NUM_SEGMENTS = 16
IMAGES_BUCKET_DIR = 'momentsintime/images'  # input images storage prefix
MODEL_BUCKET_KEY = 'momentsintime/models/moments_RGB_resnet50_imagenetpretrained'
```


```python
if not os.access(WEIGHT_FILE, os.W_OK):
    os.system('wget ' + '/'.join(ROOT_URL, WEIGHT_FILE))

# Load pretrained resnet50 model
model = models.load_model(WEIGHT_FILE)

buf = io.BytesIO()
torch.save(model, buf)

# Save model to cloud storage
cloud_storage = CloudStorage()
cloud_storage.put_data(key=MODEL_BUCKET_KEY, data=buf)
```


```python
def predict_video(categories, transform, cloud_storage, video_key):
    start = time.time()
    model_bytes = cloud_storage.get_data(MODEL_BUCKET_KEY)
    model = torch.load(io.BytesIO(model_bytes))
    print('Time to get the model:', round(time.time() - start, 3))
    model.eval()

    # Obtain video frames
    start = time.time()
    video_bytes = cloud_storage.get_data(video_key)
    print('Time to get the video:', round(time.time() - start, 3))

    local_video_key = '/tmp/image_to_predict.mp4'
    with open(local_video_key, 'wb') as f:
        f.write(video_bytes)
        frames = extract_frames(local_video_key, NUM_SEGMENTS)
    os.remove(local_video_key)

    # Prepare input tensor [num_frames, 3, 224, 224]
    input = torch.stack([transform(frame) for frame in frames])

    # Make video prediction
    with torch.no_grad():
        logits = model(input)
        h_x = F.softmax(logits, 1).mean(dim=0)
        probs, idx = h_x.sort(0, True)

    # Output the prediction
    output = {}
    for i in range(0, 5):
        output[categories[idx[i]]] = round(float(probs[i]), 5)

    return output
```


```python
video_keys = cs.list_tmp_data(prefix=IMAGES_BUCKET_DIR)
print(video_keys[:10])

# Get dataset categories
categories = models.load_categories()

# Load the video frame transform
transform = models.load_transform()

with Pool() as pool:
    iterable = [(categories, transform, cs, k) for k in video_keys]
    res = pool.map_async(func=predict_video, iterable=iterable)
    print(res.get())
```


```python

```


```python

```


```python

```


```python

```
